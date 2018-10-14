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
from gst import gst_file_reader
from annotations import draw_txt
import utils

parser = argparse.ArgumentParser()
parser.add_argument("--gst",help="stream with gst", action='store_true')
parser.add_argument("--nosync", help="dont sync videos", action='store_true')
parser.add_argument("--path",help="dir path")
args = parser.parse_args()



if __name__=='__main__':
    print('nosync',args.nosync)
    reader = gst_file_reader(args.path,nosync = args.nosync)
    #fd = open(args.path+'/data.pkl','rb')
    fd = open(args.path+'/viewer_data.pkl','rb')
    sx,sy=config.pixelwidthx,config.pixelwidthy
    join=np.zeros((sy,sx*2,3),'uint8')
    vis_data = {}
    main_data  ={}
    while 1:
        images,fcnt=reader.__next__()
        print('fnum in image',fcnt)
        while 1:
            ret=pickle.load(fd)
            print('topic=',ret[0])
            if ret[0]==config.topic_comp_vis:
                vis_data=ret[1]
                print('fnum in vis',vis_data['fnum'])
                if vis_data['fnum']>=fcnt:
                    break
            if ret[0]==config.topic_mav_telem:
                #data=pickle.loads(ret[1])
                data=ret[1]
            if ret[0]==config.topic_main_telem:
                #main_data.update(pickle.loads(ret[1]))
                main_data.update(ret[1])
                #if 'mavpackettype' not in data:
                #    print(data)

        if images[0] is not None and images[1] is not None:
            if 'draw_rectsl' in vis_data:
                for rectp in vis_data['draw_rectsr']:
                    cv2.rectangle(images[1],*rectp)
                for rectp in vis_data['draw_rectsl']:
                    cv2.rectangle(images[0],*rectp)
            #print(images[0].shape,join.shape)
            join[:,0:sx,:]=images[0]
            join[:,sx:,:]=images[1]
            draw_txt(join,vis_data,main_data)
            cv2.imshow('3dviewer',join)
            #cv2.imshow('left',images[0])
            #cv2.imshow('right',images[1])
        k=cv2.waitKey(0)
        if k==ord('q'):
            break


### fmt_cnt_l,imgl,imgr=imgget.__next__()
###                fmt_cnt_r=fmt_cnt_l
###                img=imgl

