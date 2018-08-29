#!/bin/bash
##
PATH=/local/ori/anaconda3.6/bin:$PATH
tmux kill-session -t rov_companion
tmux new-session -d -s rov_companion

tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v

tmux select-pane -t 0
tmux set -g pane-border-format "#{pane_index} #T"
printf '\033]2;ROV MAIN\033\\'
tmux send-keys "python main.py" ENTER


tmux select-pane -t 1
tmux send-keys "cd algs && python v3d.py" ENTER
#tmux send-keys "cd algs && python v3d.py --cvshow" ENTER

tmux select-pane -t 2
#printf '\033]2;My Pane Title 3\033\\'

tmux select-pane -t 2
#printf '\033]2;My Pane Title 3\033\\'

tmux att
