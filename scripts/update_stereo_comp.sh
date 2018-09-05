#!/bin/bash
#git push origin master && ssh stereo@stereo-UP-APL01 "cd bluerov && git checkout dev && git merge master"
git checkout master && \
git pull ssh://stereo@localhost:2222/home/stereo/bluerov master && \
git push ssh://stereo@localhost:2222/home/stereo/bluerov master && \
./sshstereo.sh "cd bluerov && git merge master" && \
git checkout dev

