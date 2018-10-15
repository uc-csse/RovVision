#!/bin/bash
tmux new-session -d -s run_pppd
tmux send-keys "source /home/stereo/bluerov/scripts/detect_usbs.sh" ENTER
tmux send-keys "while true; do" ENTER
tmux send-keys "pppd  -detach noipx nocrtscts maxfail 0 10.0.0.1:10.0.0.2 /dev/\$SERIAL_USB 2000000" ENTER
tmux send-keys "sleep 5" ENTER
tmux send-keys "done" ENTER
