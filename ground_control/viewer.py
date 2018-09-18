# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import sys,os,time
from datetime import datetime
sys.path.append('../')
import zmq
import pickle
import select
import struct
import cv2,os
import argparse
import numpy as np
import config
from gst import init_gst_reader,get_imgs

parser = argparse.ArgumentParser()
parser.add_argument("--gst",help="stream with gst", action='store_true')
args = parser.parse_args()


context = zmq.Context()
zmq_sub_v3d = context.socket(zmq.SUB)
#zmq_sub_v3d.connect("tcp://%s:%d" % (os.environ['STEREO_IP'],config.zmq_pub_comp_vis))
zmq_sub_v3d.connect("tcp://%s:%d" % ('127.0.0.1',config.zmq_pub_comp_vis))
zmq_sub_v3d.setsockopt(zmq.SUBSCRIBE,config.topic_comp_vis)
zmq_sub_main=context.socket(zmq.SUB)
#zmq_sub_main.connect("tcp://%s:%d" % (os.environ['GCTRL_IP'],config.zmq_pub_main))
zmq_sub_main.connect("tcp://%s:%d" % ('127.0.0.1',config.zmq_pub_main))
zmq_sub_main.setsockopt(zmq.SUBSCRIBE,config.topic_main_telem)

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
        cv2.putText(img,'REC '+vd['disk_usage'],(10,200),font, 0.5,(0,0,255),1,cv2.LINE_AA)
    #cv2.putText(img,data_lines['last_cmd_str'][1],(10,250), font, 0.4,(0,0,255),1,cv2.LINE_AA)


    
if __name__=='__main__':
    init_gst_reader(2)
    sx,sy=config.pixelwidthx,config.pixelwidthy
    join=np.zeros((sy,sx*2,3),'uint8')
    vis_data = {}
    main_data  ={}
    while 1:
        images=get_imgs()

        #if all(images):
        if zmq_sub_v3d.poll(0):
            topic , data = zmq_sub_v3d.recv_multipart()
            vis_data = pickle.loads(data)
            if vis_data.get('record_state',False):
                if save_files_fds[0] is None:
                    for i in [0,1]:
                        datestr=datetime.now().strftime('%y%m%d-%H%M%S')
                        save_files_fds[i]=open('../../data/{}_{}.mp4'.format(datestr,'lr'[i]),'wb')
                    save_files_fds[2]=open('../../data/{}.bin'.format(datestr),'wb')
            else:
                save_files_fds=[None,None,None]

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

