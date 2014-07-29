#!/bin/sh
sudo ifdown wlan0
sleep 5
sudo ifup --force wlan0
sleep 5