#!/bin/bash
#rsync -avzu -e "ssh -p 2222" --exclude="*.AppImage*" --exclude="*.mp4" --exclude="*.pyc" --exclude=".git/" . stereo@localhost:/home/stereo/bluerov/
rsync -avzu -e "ssh -p 2222"  --exclude=".git" --include="*/" --include="*.sh" --include="*.py" --include="*.ino" --exclude="*" . stereo@localhost:/home/stereo/bluerov/
sleep 2
