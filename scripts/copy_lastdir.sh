#!/bin/bash
scp -r -P 2222 stereo@localhost:bluerov/data/`./sshstereo.sh "ls -t bluerov/data|head -1|tail -1"` ../../data/
