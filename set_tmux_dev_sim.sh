#!/bin/bash
##
PATH=/local/ori/anaconda3.6/bin:$PATH
tmux kill-session -t rov_dev
tmux new-session -d -s rov_dev

tmux split-window -h
#tmux split-window -v
tmux select-pane -t 1
tmux split-window -v
tmux select-pane -t 1
tmux split-window -v
tmux select-pane -t 3
tmux split-window -v
tmux split-window -v
tmux select-pane -t 3
tmux split-window -v
tmux select-pane -t 1
tmux send-keys "SIMROV= python main.py --sim" ENTER

tmux select-pane -t 2
tmux send-keys "cd algs && SIMROV= python v3d.py --gst --save" ENTER
#tmux send-keys "cd algs && python v3d.py --cvshow" ENTER

tmux select-pane -t 3
tmux send-keys "cd ground_control && ./QGroundControl.AppImage" ENTER

tmux select-pane -t 4
tmux send-keys "cd ground_control && python joy_rov.py" ENTER

tmux select-pane -t 5
tmux send-keys "cd ground_control && SIMROV= python viewer.py" ENTER

tmux select-pane -t 0
tmux send-keys "echo 'run vim here'" ENTER

tmux select-pane -t 6
tmux send-keys "cd web && FLASK_RUN_PORT=8090 FLASK_APP=server.py flask run" ENTER
tmux att
