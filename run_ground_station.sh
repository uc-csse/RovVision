#!/bin/bash
##
source set_env_oper.sh
PATH=/local/ori/anaconda3.6/bin:$PATH
tmux kill-session -t rov_groud_station
tmux new-session -d -s rov_groud_station

tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v
tmux split-window -v

tmux select-pane -t 0
tmux set -g pane-border-format "#{pane_index} #T"
printf '\033]2;GROUND CONTROL\033\\'
tmux send-keys "cd ground_control && ./QGroundControl.AppImage" ENTER

tmux select-pane -t 1
tmux send-keys "cd ground_control && python joy_rov.py" ENTER

tmux select-pane -t 4
tmux send-keys "cd ground_control && python viewer.py" ENTER

tmux select-pane -t 2
tmux send-keys "cd ground_control && python udp_route.py" ENTER

tmux select-pane -t 3
tmux send-keys "cd web && FLASK_RUN_PORT=8090 FLASK_APP=server.py flask run" ENTER
tmux att
