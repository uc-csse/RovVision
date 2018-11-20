# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import glob
import time,sys
from subprocess import Popen
cmdfmt="convert {0}.ppm  /tmp/tmp{1}.png && cwebp -quiet -mt -q 90  /tmp/tmp{1}.png -o {0}.webp && rm {0}.ppm"
flist = glob.glob('*/*.ppm')
pl=[Popen('sleep 1'.split()) for _ in range(6)]
print('files to convert',len(flist))
for ind,f in enumerate(flist):
    print(ind,f)
    #free_list=[pr.poll() is None for pr in pl]
    while 1:
        found_free=False
        for i,pr in enumerate(pl):
            st=pr.poll()
            #print('---',st)
            cmd=''
            if st==0:
                print(f,ind,'/',len(flist))
                cmd=cmdfmt.format(f[:-4],i)
                #print(cmd)
                pl[i]=Popen(cmd,shell=True)
                #pl[i]=Popen("echo %d && sleep 2"%i,shell=True)
                found_free=True
                break
            elif st==None:
                pass
            else:
                print('got error code',st)
                print(cmd)
                sys.exit(0)
        if found_free:
            time.sleep(0.01)
            break
        else:
            time.sleep(0.2)
            #print('sleep')

