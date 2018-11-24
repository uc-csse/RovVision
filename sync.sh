#!/bin/bash
#rsync -avzu -e "ssh -p 2222" --exclude="*.AppImage*" --exclude="*.mp4" --exclude="*.pyc" --exclude=".git/" . stereo@localhost:/home/stereo/bluerov/
rsync -avzu -e "ssh -p 2222" --include="*/" --include="*.py" --exclude="*" . stereo@localhost:/home/stereo/bluerov/
