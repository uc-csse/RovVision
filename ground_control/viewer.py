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
from gst import init_gst_reader,get_imgs,set_files_fds,get_files_fds
from annotations import draw_txt
import utils

parser = argparse.ArgumentParser()
parser.add_argument("--gst",help="stream with gst", action='store_true')
args = parser.parse_args()


zmq_sub_v3d=utils.subscribe([config.topic_comp_vis],config.zmq_pub_comp_vis)
zmq_sub_main=utils.subscribe([config.topic_main_telem],config.zmq_pub_main)

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
                if get_files_fds()[0] is None:
                    fds=[]
                    for i in [0,1]:
                        datestr=datetime.now().strftime('%y%m%d-%H%M%S')
                        fds.append(open('../../data/{}_{}.mp4'.format(datestr,'lr'[i]),'wb'))
                    set_files_fds(fds)
                    #save_files_fds[2]=open('../../data/{}.bin'.format(datestr),'wb')
            else:
                set_files_fds([None,None])

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

