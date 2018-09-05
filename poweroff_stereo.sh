#!/bin/bash
printf '\033]2;STEREO\033\\'
./scripts/sshstereo.sh -t "sudo poweroff"
