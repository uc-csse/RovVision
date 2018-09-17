# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
############# gst ########
#to watch
#gst-launch-1.0 -e -v udpsrc port=5700 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
#gst-launch-1.0 -e -v udpsrc port=5701 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
from subprocess import Popen,PIPE
import sys,time,select
import config

gst_pipes=None
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
    
#############################


