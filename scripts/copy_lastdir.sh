#!/bin/bash
LAST_DIR=`./sshstereo.sh "cd bluerov/data && ls -t |head -1|tail -1"`
echo $LAST_DIR
#scp -r -P 2222 stereo@localhost:bluerov/data/`./sshstereo.sh "ls -t bluerov/data|head -1|tail -1"` ../../data/
ssh -p 2222 stereo@localhost "cd bluerov/data && tar czf - $LAST_DIR"  | tar xvzf - -C ../../data  
