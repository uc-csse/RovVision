#syncing data:
from stereo to laptop:
cd ~/data
rsync -avzu -e "ssh" stereo@stereo-UP-APL01:bluerov/data/181121-* ./

from laptop to network:
cd ~/data
rsync -avzu -e "ssh" 181121-11* username@linux.cosc.canterbury.ac.nz:/home/cosc/research/CVlab/bluerov_data/

#only pickles
rsync -avzu --excluse * --include *.pkl -e "ssh" 181121-11* username@linux.cosc.canterbury.ac.nz:/home/cosc/research/CVlab/bluerov_data/
