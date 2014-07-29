import RPi.GPIO as GPIO
import time
import os
import thread
import pygame

length = 7
maxFiles = 20
iterator = 0
newVideo = False
password = "theslamcam"

#init hardware
GPIO.setwarnings( False )
GPIO.setmode( GPIO.BCM )
GPIO.setup( 24, GPIO.IN, pull_up_down = GPIO.PUD_UP )
GPIO.setup( 17, GPIO.OUT )
for i in range( 0, 2 ): #blink twice to indicate script is running
        GPIO.output( 17, True )
        time.sleep( .5 )
        GPIO.output( 17, False )
        time.sleep( .5 )

#check for IP addressess
def check_internet():
        if(os.system("ping -c 2 -t 5 10.12.12.1") > 0):
                print("Not connected to the router")
                for i in range( 0, 5 ): #blink slowly to indicate issue with router communication
                        GPIO.output( 17, True )
                        time.sleep( 1 )
                        GPIO.output( 17, False )
                        time.sleep( 1 )
        elif (os.system("ping -c 2 -t 5 10.5.5.9") > 0):
                print("GoPro is not connected")
                 for i in range( 0, 20 ): #blink a bunch of times if the gopro is not found
                        GPIO.output( 17, True )
                        time.sleep( .1 )
                        GPIO.output( 17, False )
                        time.sleep( .1 )
                os.system("sudo /home/pi/Documents/slamCam/restart_gopro.sh")
        if (os.system("ping -c 2 google.com") > 0):
                print("Not connected to the internet")
                for i in range (0, 10 ): #two quick blinks indicate we can't reach the outside world
                        GPIO.output( 17, True)
                        time.sleep( .05 )
                        GPIO.output( 17, False )
                        time.sleep(.05 )
                        GPIO.output( 17, True)
                        time.sleep( .05 )
                        GPIO.output( 17, False )
                        time.sleep( .2 )
                os.system("sudo /home/pi/Documents/slamCam/restart_internet.sh")
                check_internet()

check_internet()


#set gopro to video mode
os.system( "curl 'http://10.5.5.9/camera/CM?t=" + password + "&p=%00'" )
os.system( "curl 'http://10.5.5.9/camera/FV?t=" + password + "&p=%00'" )

#init sound out
os.system( "sudo amixer cset numid=1 -- 200" )
pygame.mixer.init()
pygame.mixer.music.load( "/home/pi/Documents/slamCam/slam.aiff" )
pygame.mixer.music.set_volume( 1.0 )


path = "/home/pi/Documents/slamCam/videos/10.5.5.9:8080/videos/DCIM/104GOPRO/"
items = os.listdir( path )
filelist = []
new_videos = []

for filenames in items:
        filelist.append( filenames )

print( "filelist: " + ', '.join( filelist ))


def buttonPressed_callback( channel ):
        pygame.mixer.music.set_volume( 1.0 )
        pygame.mixer.music.play()
        time.sleep( .4 )
        for i in range( 0, 4 ):
                GPIO.output( 17, True )
                time.sleep( .325 )
                GPIO.output( 17, False )
                time.sleep( .325 )
        captureVideo( length )


def captureVideo( videoLength ):
        GPIO.output( 17, True ) #led on 
        #start capture
        os.system( "curl 'http://10.5.5.9/bacpac/SH?t=" + password + "&p=%01'" )
        #wait 6 seconds
        time.sleep( videoLength )
        GPIO.output( 17, False ) #led off
        #stop capture
        os.system( "curl 'http://10.5.5.9/bacpac/SH?t=" + password + "&p=%00'" )
        print( "video captured" )
        global newVideo
        newVideo = True

def moveVideoToPi( threadName, priority ):
        os.system( "wget -c -r -q -A.MP4 -N -P /home/pi/Documents/slamCam/videos/ 'http://10.5.5.9:8080/videos/DCIM/104GOPRO/'" )
        print( "video moved to pi" )
        get_new_videos( filelist, path )
        thread.exit()

def get_new_videos( filelist, path ):
        files = os.listdir( path )
        for filename in files:
                filename_in_caps = filename.upper()
                if filename_in_caps.endswith('.MP4'):
                        try:
                                filelist.index( filename )
                        except ValueError:
                                global new_videos
                                try:
                                        new_videos.index( filename )
                                except ValueError:
                                        new_videos.append( filename )
                                        print( "new videos: " + ', '.join( new_videos ))
                                        uploadVideo( filename )

def uploadVideo( filename ):
        global filelist
        global new_videos
        global iterator
        global maxFiles

        exit_code = os.system( "curl -i -F file=@" + path + filename + " http://slamcam.wkcreativetech.com/api/vine/add" )
        print( "exit code: " + str( exit_code))
        if exit_code == 0:
                try 
                        filelist.append( filename )
                        new_videos.remove( filename )
                        print( "uploaded " + filename )
                        print( "new new videos list: " + ', '.join( new_videos ))
                        print( "new file list: " + ', '.join( filelist ))
                        iterator += 1
                        print( "iterator: %d" % iterator )
                        if iterator >= maxFiles:
                                if new_videos:
                                        for filename in new_videos:
                                                uploadVideo( filename )
                                else:
                                        clearMemoryCards()
                except: 
                        pass
     
        else:
                print( "exit code: " + str( exit_code ))
                print( "no good new videos remain: " + ', '.join( new_videos ))

def clearMemoryCards():
        print( "clearing now" )
        os.system( "sudo rm " + path + "/*" ) #clear all files from raspberry pi memory
        os.system( "curl 'http://10.5.5.9/camera/DA?t=" + password + "'" ) #clear all files from gopro
        global iterator
        iterator = 0
        #thread.exit()

GPIO.add_event_detect( 24, GPIO.RISING, callback=buttonPressed_callback, bouncetime = 13000 )

#new_videos = get_new_videos( filelist, path )

while True:

        if newVideo == True:
                thread.start_new_thread( moveVideoToPi, ("video to pi", 2))
                newVideo = False

GPIO.cleanup()
