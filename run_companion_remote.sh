#!/bin/bash
printf '\033]2;STEREO\033\\'
./scripts/sshstereo.sh "tmux kill-session -t rov_companion"
./scripts/sshstereo.sh -t "cd bluerov && source set_env_oper.sh && ./run_companion.sh"  

