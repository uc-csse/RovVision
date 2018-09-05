#!/bin/bash
printf '\033]2;STEREO\033\\'
ssh -t pi@192.168.2.2 "echo 'press key to power off' && read -n1 && sudo poweroff"
