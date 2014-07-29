
#!/bin/sh
sudo ifdown wlan0
sudo ifdown eth0
sleep 5
sudo ifup --force eth0
sudo ifup --force wlan0
sleep 5