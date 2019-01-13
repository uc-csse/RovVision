#!/bin/bash
LOCALS=""
REMOTES=""

LP="6760 6761 8877 9921 5900 5901 6600 5566"
RP="9117 9931"

for i in $LP;do
  LOCALS="$LOCALS -L $i:127.0.0.1:$i"
done
for i in $RP;do
  REMOTES="$REMOTES -R $i:127.0.0.1:$i"
done

#STEREO_IP=192.168.3.17
#RASPPI_IP=192.168.2.2
#STEREO_IP=10.0.0.1
#RASPPI_IP=raspberrypi

STATION_ADDR=labuser@cs18018hr

STEREO_IP=10.0.0.1
#echo $LOCALS
CMD="ssh -t $LOCALS $REMOTES -L 2222:localhost:22 $STATION_ADDR"
echo $CMD
$CMD
