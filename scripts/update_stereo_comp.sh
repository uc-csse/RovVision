#!/bin/bash
git push origin master && ssh stereo@stereo-UP-APL01 "cd bluerov && git checkout dev && git merge master"

