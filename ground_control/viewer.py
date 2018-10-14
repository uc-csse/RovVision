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
import image_enc_dec

parser = argparse.ArgumentParser()
parser.add_argument("--gst",help="stream with gst", action='store_true')
args = parser.parse_args()

subs_socks=[]
subs_socks.append(utils.subscribe([config.topic_comp_vis],config.zmq_pub_comp_vis))
subs_socks.append(utils.subscribe([config.topic_main_telem],config.zmq_pub_main))


if __name__=='__main__':
    init_gst_reader(2)
    sx,sy=config.pixelwidthx,config.pixelwidthy
    join=np.zeros((sy,sx*2,3),'uint8')
    vis_data = {}
    main_data  ={}
    data_file_fd=None
    rcv_cnt=0
    while 1:
        images=get_imgs()
        rcv_cnt+=1
        #if all(images):
        socks=zmq.select(subs_socks,[],[],0.001)[0]
        for sock in socks:
            ret = sock.recv_multipart()
            topic , data = ret
            if ret[0]==config.topic_comp_vis:
                vis_data=pickle.loads(ret[1])
                break
            if ret[0]==config.topic_mav_telem:
                mav_data=pickle.loads(ret[1])
            if ret[0]==config.topic_main_telem:
                main_data.update(pickle.loads(ret[1]))

            if vis_data.get('record_state',False):
                if get_files_fds()[0] is None:
                    fds=[]
                    datestr=vis_data['record_date_str']
                    save_path='../../data/'+datestr
                    os.mkdir(save_path)
                    for i in [0,1]:
                        #datestr=datetime.now().strftime('%y%m%d-%H%M%S')
                        fds.append(open(save_path+'/vid_{}.mp4'.format('lr'[i]),'wb'))
                    set_files_fds(fds)
                    data_file_fd=open(save_path+'/viewer_data.pkl','wb')
            else:
                set_files_fds([None,None])
                data_file_fd=None

            if data_file_fd is not None:
                pickle.dump(ret,data_file_fd,-1)
                pickle.dump(['viewer_data',{'rcv_cnt':rcv_cnt}],data_file_fd,-1)

        #print('-1-',main_data)

        if images[0] is not None and images[1] is not None:
            fmt_cnt_l=image_enc_dec.decode(images[0])
            fmt_cnt_r=image_enc_dec.decode(images[1])
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

