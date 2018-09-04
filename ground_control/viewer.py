# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import sys,os,time
sys.path.append('../')
import zmq
import pickle
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


context = zmq.Context()
zmq_sub_v3d = context.socket(zmq.SUB)
zmq_sub_v3d.connect("tcp://127.0.0.1:%d" % config.zmq_pub_comp_vis)
zmq_sub_v3d.setsockopt(zmq.SUBSCRIBE,config.topic_comp_vis)
zmq_sub_main=context.socket(zmq.SUB)
zmq_sub_main.connect("tcp://127.0.0.1:%d" % config.zmq_pub_main)
zmq_sub_main.setsockopt(zmq.SUBSCRIBE,config.topic_main_telem)

############# gst ########
gst_pipes=None
sx,sy=640,512
shape = (sy, sx, 3)

gst_pipes = None
def init_gst(npipes):
    global gst_pipes
    #cmd='gst-launch-1.0 -e -v udpsrc port={} ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw, format=RGB8P ! fdsink'
    if 1: #h264
        cmd='gst-launch-1.0 -q udpsrc port={} ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! decodebin ! videoconvert ! video/x-raw,height={},width={},format=RGB ! fdsink'
    if 0:
        cmd='gst-launch-1.0 -q udpsrc port={} ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,height={},width={},format=RGB ! fdsink'
    
    gst_pipes=[]
    for i in range(npipes):
        gcmd = cmd.format(5760+i,sy,sx)
        p = Popen(gcmd, shell=True, bufsize=1024*10, stdout=PIPE, stderr=sys.stderr, close_fds=False)
        gst_pipes.append(p)

images=[None,None]
def get_imgs():
    global gst_pipes,images
    for i in range(len(images)):
        if len(select.select([gst_pipes[i].stdout],[],[],0.001)[0])>0 :
            data=gst_pipes[i].stdout.read(sx*sy*3)
            images[i]=np.fromstring(data,'uint8').reshape([sy,sx,3])

def draw_txt(img,vd,md):
    font = cv2.FONT_HERSHEY_SIMPLEX
    #print('-2-',md)
    if 'ts' in md and 'range_avg' in vd:
        line1='{:4.1f}s R{:3.2f}m'.format(md['ts'],vd['range_avg'])
        cv2.putText(img,line1,(10,50), font, 0.5,(0,0,255),1,cv2.LINE_AA)

    if 'lock' in md and md['lock']: 
        line2='{:>4}bf {:4.2f}LR'.format(md['fb_cmd'],md['lock_range'])
        if 'ud_cmd' in md:
            line2+=' {:>4}ud {:>4}lr'.format(md['ud_cmd'],md['lr_cmd'])
        cv2.putText(img,line2,(10,100), font, 0.5,(0,0,255),1,cv2.LINE_AA)
    if vd.get('record_state',False):
        cv2.putText(img,'REC',(10,200),font, 0.5,(0,0,255),1,cv2.LINE_AA)
    #cv2.putText(img,data_lines['last_cmd_str'][1],(10,250), font, 0.4,(0,0,255),1,cv2.LINE_AA)


    

if __name__=='__main__':
    init_gst(2)
    join=np.zeros((sy,sx*2,3),'uint8')
    vis_data = {}
    main_data  ={}
    while 1:
        get_imgs()

        #if all(images):
        if zmq_sub_v3d.poll(0):
            topic , data = zmq_sub_v3d.recv_multipart()
            vis_data = pickle.loads(data)
        if zmq_sub_main.poll(0):
            topic , data = zmq_sub_main.recv_multipart()
            main_data = pickle.loads(data)
        #print('-1-',main_data)

        if images[0] is not None and images[1] is not None:
            if 'draw_rectsl' in vis_data:
                for rectp in vis_data['draw_rectsr']:
                    cv2.rectangle(images[1],*rectp)
                for rectp in vis_data['draw_rectsl']:
                    cv2.rectangle(images[0],*rectp)
            #print(images[0].shape,join.shape)
            join[:,0:sx,:]=images[0]
            join[:,sx:,:]=images[1]
            images=[None,None]
            draw_txt(join,vis_data,main_data)
            cv2.imshow('3dviewer',join)
            #cv2.imshow('left',images[0])
            #cv2.imshow('right',images[1])
        k=cv2.waitKey(10)
        if k==ord('q'):
            for p in gst_pipes:
                p.terminate()
                p.poll()
            break

