# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# to copy data.pkl
# sim:
# cd into data dir and then
# > scp -P 2222 oga13@localhost:projects/bluerov/data/$(basename $( pwd ))/data.pkl .

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
import explore

parser = argparse.ArgumentParser()
parser.add_argument("--nowait",help="run all not wait for keyboard untill framenum or 0 till the end", default=-1, type=int)
parser.add_argument("--nosingle",help="dont use the single files only the stream", action='store_true')
parser.add_argument("--nosync", help="dont sync videos", action='store_true')
parser.add_argument("--novid", help="ignore video", action='store_true')
parser.add_argument("--path",help="dir path")
parser.add_argument("--bs",help="history buff size",type=int ,default=1000)
args = parser.parse_args()

file_path_fmt=args.path+'/{}{:08d}'#.ppm'


#def equalize(img):
#    img_yuv=cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
#    img_yuv[:,:,2]=cv2.equalizeHist(img_yuv[:,:,2])
#    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)


def equalize(img):
    b, g, r = cv2.split(img)
    red = cv2.equalizeHist(r)
    green = cv2.equalizeHist(g)
    blue = cv2.equalizeHist(b)
    return cv2.merge((blue, green, red))

imbuff=[None for i in range(50)]

if __name__=='__main__':
    print('nosync',args.nosync)
    if not args.novid:
        reader = gst_file_reader(args.path,nosync = args.nosync)
    #fd = open(args.path+'/data.pkl','rb')
    if os.path.isfile(args.path+'/data.pkl'):
        fd = open(args.path+'/data.pkl','rb')
    else:
        fd = open(args.path+'/viewer_data.pkl','rb')
    sx,sy=config.pixelwidthx,config.pixelwidthy
    join=np.zeros((sy,sx*2,3),'uint8')
    vis_data = {}
    main_data  ={}
    main_data_hist = []
    vis_data_hist = []
    fcnt=-1
    from_buff=False
    while 1:
        hist_buff_ind=fcnt%len(imbuff)
        if not args.novid and imbuff[hist_buff_ind]!=None and imbuff[hist_buff_ind][0]==fcnt:
            fcnt,images,vis_data,main_data=imbuff[hist_buff_ind]
            from_buff=True
        else:
            if not args.novid:
                images,fcnt=reader.__next__()
            else:
                fcnt+=1
                images=[None,None]
            from_buff=False
            print('fnum in image',fcnt)
            while fcnt>-1:
                try:
                    ret=pickle.load(fd)
                except EOFError:
                    print('No more data')
                    if args.novid:
                        explore.plot_graphs(main_data_hist,vis_data_hist)
                        sys.exit(0)
                    break
                print('topic=',ret[0])
                if ret[0]==config.topic_comp_vis:
                    vis_data=ret[1]
                    print('fnum in vis',vis_data['fnum'])
                    vis_data_hist.append(vis_data)
                    if len(vis_data_hist)>args.bs:
                        vis_data_hist.pop(0)
                    if vis_data['fnum']>=fcnt:
                        break
                if ret[0]==config.topic_mav_telem:
                    #data=pickle.loads(ret[1])
                    data=ret[1]
                    #'mavpackettype': 'VFR_HUD'
                    if data['mavpackettype'] in { 'VFR_HUD' , 'SERVO_OUTPUT_RAW' }:
                        print('mav telem',data)
                if ret[0]==config.topic_main_telem:
                    #main_data.update(pickle.loads(ret[1]))
                    main_data.update(ret[1])
                    main_data_hist.append(main_data.copy())
                    #if 'mavpackettype' not in data:
                    if len(main_data_hist)>args.bs:
                        main_data_hist=main_data_hist[1:]
                    #    print(data)
            if not args.novid and fcnt>0:
                hist_buff_ind=fcnt%len(imbuff)
                imbuff[hist_buff_ind]=(fcnt,images,vis_data,main_data)

        imgs_raw=[None,None]
        if fcnt >0 and images[0] is not None and images[1] is not None:
            #if 1 or not  from_buff:
            for i in [0,1]:
                if not args.nosingle:
                    for ext in ['.ppm','.png','.webp']:
                        fname=file_path_fmt.format('lr'[i],fcnt)+ext
                        if os.path.isfile(fname):
                            imgs_raw[i]=cv2.imread(fname)
                            images[i]=imgs_raw[i][::2,::2,:].copy()
                            break

                    #images[i]=cv2.imread(fname)[:,:,::-1].copy()
                if imgs_raw[i] is None:
                    imgs_raw[i]=images[i].copy()#[:,:,::-1].copy()
            
                


            if 'draw_rectsl' in vis_data:
                for rectp in vis_data['draw_rectsr']:
                    cv2.rectangle(images[1],*rectp)
                for rectp in vis_data['draw_rectsl']:
                    cv2.rectangle(images[0],*rectp)
            

            #print(images[0].shape,join.shape)
            join[:,0:sx,:]=images[0]#[:,:,::-1]
            join[:,sx:,:]=images[1]#[:,:,::-1]

            draw_txt(join,vis_data,main_data)
            if explore.is_data_file(args.path,fcnt):
                cv2.circle(join,(0,0), 15, (0,0,255), -1)
            cv2.imshow('3dviewer',join)
            #cv2.imshow('left',images[0])
            #cv2.imshow('right',images[1])
            if args.nowait > fcnt:
                k=cv2.waitKey(1)
            else:
                k=cv2.waitKey(0)
            if k%256==ord('q'):
                break
            if k%256==ord('i'):
                explore.plot_raw_images(imgs_raw,args.path,fcnt)
            if k%256==ord('p'):
                explore.plot_graphs(main_data_hist,vis_data_hist)
            if k%256==8:
                fcnt-=1 
            else:
                fcnt+=1


### fmt_cnt_l,imgl,imgr=imgget.__next__()
###                fmt_cnt_r=fmt_cnt_l
###                img=imgl

