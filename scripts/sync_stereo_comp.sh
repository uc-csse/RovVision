#!/bin/bash
#git push origin master && ssh stereo@stereo-UP-APL01 "cd bluerov && git checkout dev && git merge master"
rsync -avz -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
	--include="*/" --include="*.py" --exclude="*"
	--progress ../bluerov stereo@localhost:2222/home/stereo/bluerov

