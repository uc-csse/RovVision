# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
############# gst ########
#to watch
#gst-launch-1.0 -e -v udpsrc port=5700 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
#gst-launch-1.0 -e -v udpsrc port=5701 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
from subprocess import Popen,PIPE
import sys,time,select,os
import numpy as np
import config
import image_enc_dec
############# gst wirite #########
gst_pipes=None
send_cnt=[0,0]
def init_gst(sx,sy,npipes):
    global gst_pipes
    #cmd="gst-launch-1.0 {}! x264enc tune=zerolatency  bitrate=500 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
    if 0: #h264 stream
        cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=300 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
        gstsrc = 'fdsrc ! videoparse width={} height={} framerate=30/1 format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
    
    if 1:
        #cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=500 key-int-max=15 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
        cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=500 key-int-max=50 ! tcpserversink port={}"
        gstsrc = 'fdsrc ! videoparse width={} height={} format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
    if 0:
        gstsrc = 'fdsrc ! videoparse width={} height={} framerate=30/1 format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
       
        cmd="gst-launch-1.0 {} ! jpegenc quality=20 ! rtpjpegpay ! udpsink host=192.168.2.1 port={}"

    gst_pipes=[]
    for i in range(npipes):
        gcmd = cmd.format(gstsrc,config.gst_ports[i])
        p = Popen(gcmd, shell=True, bufsize=0,stdin=PIPE, stdout=sys.stdout, close_fds=False)
        gst_pipes.append(p)

def send_gst(imgs):
    global gst_pipes
    for i,im in enumerate(imgs):
        time.sleep(0.001)
        if len(select.select([],[gst_pipes[i].stdin],[],0)[1])>0:
            gst_pipes[i].stdin.write(im.tostring())
            send_cnt[i]+=1

def init_gst_files(sx,sy):
   pass


############# gst read #########
gst_pipes_264=None
sx,sy=config.pixelwidthx, config.pixelwidthy
shape = (sx, sy, 3)

def init_gst_reader(npipes):
    global gst_pipes,gst_pipes_264
    if 1: #h264
        cmd='gst-launch-1.0 tcpclientsrc port={} ! identity sync=true  ! tee name=t ! queue ! filesink location=fifo_264_{}  sync=false  t. ! queue !'+\
        ' h264parse ! decodebin ! videoconvert ! video/x-raw,height={},width={},format=RGB ! filesink location=fifo_raw_{}  sync=false'
    if 0:
        cmd='gst-launch-1.0 -q udpsrc port={} ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,height={},width={},format=RGB ! fdsink'
    
    gst_pipes=[]
    gst_pipes_264=[]
    os.system('rm fifo_*')
    cmds=[]
    for i in range(npipes):
        fname_264='fifo_264_'+'lr'[i]
        os.mkfifo(fname_264)
        r = os.open(fname_264,os.O_RDONLY | os.O_NONBLOCK)
        fname_raw='fifo_raw_'+'lr'[i]
        os.mkfifo(fname_raw)
        r1 = os.open(fname_raw,os.O_RDONLY | os.O_NONBLOCK)
        gcmd = cmd.format(config.gst_ports[i],'lr'[i],sy,sx,'lr'[i])
        print(gcmd)
        cmds.append(gcmd)
        gst_pipes_264.append(r)
        gst_pipes.append(r1)
    for cmd in cmds: #start together 
        Popen(cmd, shell=True, bufsize=0)

images=[None,None]
save_files_fds=[None,None]
def get_files_fds():
    return save_files_fds

def set_files_fds(fds):
    for i in [0,1]:
        save_files_fds[i]=fds[i]

def get_imgs():
    global images
    for i in range(len(images)):
        if len(select.select([ gst_pipes[i] ],[],[],0.001)[0])>0 :
            data=os.read(gst_pipes[i],sx*sy*3)
            images[i]=np.fromstring(data,'uint8').reshape([sy,sx,3])
        if len(select.select([ gst_pipes_264[i] ],[],[],0.001)[0])>0:
            data=os.read(gst_pipes_264[i],1*1000*1000)
            if save_files_fds[0] is not None:
                save_files_fds[i].write(data)
    return images


############ gst from files #################
import glob
def read_image_from_pipe(p):
    if len(select.select([p],[],[],0.1)[0])==0:
        return None,-1
    data=os.read(p,sx*sy*3)
    if data:
        img=np.fromstring(data,'uint8').reshape([sy,sx,3])
        fmt_cnt=image_enc_dec.decode(img)
    else:
        print('Error no data')
        sys.exit(0)
    return img,fmt_cnt

def gst_file_reader(path, nosync):
    global images
    cmd='gst-launch-1.0 filesrc location={} ! '+\
        ' h264parse ! decodebin ! videoconvert ! video/x-raw,height={},width={},format=RGB ! filesink location=fifo_raw_{}  sync=false'
    gst_pipes=[]
    os.system('rm fifo_raw_*')
  
    for i in [0,1]:
        fname_raw='fifo_raw_'+'lr'[i]
        os.mkfifo(fname_raw)
        r1 = os.open(fname_raw,os.O_RDONLY | os.O_NONBLOCK)
        fname=glob.glob(path+'/*_'+'lr'[i]+'.mp4')[0]
        gcmd = cmd.format(fname,sy,sx,'lr'[i])
        print(gcmd)
        gst_pipes.append(r1)
        Popen(gcmd, shell=True)
    
    fcnt=[-1,-1]
    while 1:
        if len(select.select(gst_pipes,[],[],0.1)[0])==len(gst_pipes):
            im1,cnt1=read_image_from_pipe(gst_pipes[0])
            im2,cnt2=read_image_from_pipe(gst_pipes[1])
            #syncing frame numbers
            if not nosync:
                if cnt1 is not None and cnt2 is not None:
                    while cnt2>cnt1:
                        im1,cnt1=read_image_from_pipe(gst_pipes[0])
                    while cnt1>cnt2:
                        im2,cnt2=read_image_from_pipe(gst_pipes[1])
            images=[im1,im2] 
            yield images,cnt1
        else:
            time.sleep(0.001)



