# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import sys,os,time
sys.path.append('../')
import zmq
import select
import struct
import cv2,os
import argparse
import numpy as np
import config
from subprocess import Popen,PIPE

parser = argparse.ArgumentParser()
parser.add_argument("--gst",help="stream with gst", action='store_true')
args = parser.parse_args()

############# gst ########
gst_pipes=None
sx,sy=640,512
shape = (sy, sx, 3)

gst_pipes = None
def init_gst(npipes):
    global gst_pipes
    #cmd='gst-launch-1.0 -e -v udpsrc port={} ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw, format=RGB8P ! fdsink'
    cmd='gst-launch-1.0 -q udpsrc port={} ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! decodebin ! videoconvert ! video/x-raw,height={},width={},format=RGB ! fdsink'

    gst_pipes=[]
    for i in range(npipes):
        gcmd = cmd.format(5700+i,sy,sx)
        p = Popen(gcmd, shell=True, bufsize=1024*10, stdout=PIPE, stderr=sys.stderr, close_fds=False)
        gst_pipes.append(p)

images=[None,None]
def get_imgs():
    global gst_pipes,images
    for i in range(len(images)):
        if len(select.select([gst_pipes[i].stdout],[],[],0.001)[0])>0 :
            data=gst_pipes[i].stdout.read(sx*sy*3)
            images[i]=np.fromstring(data,'uint8').reshape([sy,sx,3])


if __name__=='__main__':
    init_gst(2)
    join=np.zeros((sy,sx*2,3),'uint8')
    while 1:
        get_imgs()
        #if all(images):
        if images[0] is not None and images[1] is not None:
            #print(images[0].shape,join.shape)
            join[:,0:sx,:]=images[0]
            join[:,sx:,:]=images[1]
            images=[None,None]
            cv2.imshow('3dviewer',join)
            #cv2.imshow('left',images[0])
            #cv2.imshow('right',images[1])
        k=cv2.waitKey(10)
        if k==ord('q'):
            keep_running = False
            plot.send('stop')
            break

