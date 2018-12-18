#syncing data:
from stereo to laptop:
cd ~/data
rsync -avzu -e "ssh" stereo@stereo-UP-APL01:bluerov/data/181121-* ./

from laptop to network:
cd ~/data
rsync -avzu -e "ssh" 181121-11* username@linux.cosc.canterbury.ac.nz:/home/cosc/research/CVlab/bluerov_data/

#only pickles
rsync -avzu --include="*/"  --include="*.pkl" --exclude="*"  -e "ssh" 181121-11* username@linux.cosc.canterbury.ac.nz:/home/cosc/research/CVlab/bluerov_data/

#mount data
udisksctl mount -b /dev/sda



#run simulation remotely on cs18018hr
#to login
ssh labuser@cs18018hr
sudo x11vnc -auth /var/lib/mdm/:0.Xauth

vncviewer cs18018hr
run ./sim_route_cs18018hr.sh


mount ssd:
udisksctl mount -b /dev/sda
