#!/bin/bash
rsync -avzu -e "ssh -p 2222" --exclude="*.AppImage*" --exclude="*.mp4" --exclude="*.pyc" . stereo@localhost:/home/stereo/bluerov/
