#!/bin/bash
#ssh -t pi@192.168.2.2 ssh stereo@192.168.3.17 $@ 
ssh  stereo@localhost -p 2222 $@
