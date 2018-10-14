#!/bin/bash
#ssh -t pi@192.168.2.2 ssh stereo@192.168.3.17 $@ 
#date --set="$(ssh user@server 'date -u')"
# run 
# sudo visudo # add the line to the end of the file
# stereo ALL=(ALL) NOPASSWD:ALL
ssh  stereo@localhost -p 2222 sudo date -s @`( date -u +"%s" )`
