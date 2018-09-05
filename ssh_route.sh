#!/bin/bash
LOCALS=""
REMOTES=""

LP="5761 5760 8877"
RP="9117"

for i in $LP;do 
  LOCALS="$LOCALS -L $i:127.0.0.1:$i"
done
for i in $RP;do 
  REMOTES="$REMOTES -R $i:127.0.0.1:$i"
done

#echo $LOCALS
CMD="ssh -t $LOCALS $REMOTES -L 2222:localhost:2222 pi@192.168.2.2 ssh -N -L 2222:localhost:22 $LOCALS $REMOTES stereo@192.168.3.17"
echo $CMD
$CMD
