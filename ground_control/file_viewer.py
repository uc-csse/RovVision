# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# to copy data.pkl
# sim:
# cd into data dir and then
# > scp -P 2222 oga13@localhost:projects/bluerov/data/$(basename $( pwd ))/data.pkl .

import sys,os,time,traceback
from datetime import datetime
sys.path.append('../')
sys.path.append('../algs')
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
#import tracker
import tracker2 as tracker

parser = argparse.ArgumentParser()
parser.add_argument("--nowait",help="run all not wait for keyboard untill framenum or 0 till the end", default=0, type=int)
parser.add_argument("--nosingle",help="dont use the single files only the stream", action='store_true')
parser.add_argument("--nosync", help="dont sync videos", action='store_true')
parser.add_argument("--novid", help="ignore video", action='store_true')
parser.add_argument("--pub_data", help="publish data", action='store_true')
parser.add_argument("--pub_images", help="publish images", action='store_true')
parser.add_argument("--runtracker", help="run tracker on recorded vid", action='store_true')
parser.add_argument("--path",help="dir path")
parser.add_argument("--bs",help="history buff size",type=int ,default=1000)
parser.add_argument("--cc",help="color orrection matrix file",default=None)
parser.add_argument("--ccr",help="the efect of the color correction 0 to 1.0 (max 1.0)",type=float,default=1.0)
args = parser.parse_args()

file_path_fmt=args.path+'/{}{:08d}'#.ppm'

if args.cc is not None:
    c_mat = pickle.load(open(args.cc,'rb'))*args.ccr+(1.0-args.ccr)*np.eye(3)
    def apply_colorcc(img):
        return  (img.reshape((-1,3)) @ c_mat.T).clip(0,255).reshape(img.shape).astype('uint8')

if args.pub_images or args.pub_data:
    socket_pub = utils.publisher(config.zmq_local_route,'0.0.0.0')


base_name = os.path.basename(args.path)

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


def get_first_and_last(pkl_file):
    fd = open(pkl_file,'rb')
    start = -1
    end = -1
    while 1:
        try:
            ret=pickle.load(fd)
        except EOFError:
            break
        if ret[0]==config.topic_comp_vis:
            vis_data=ret[1]
            if start==-1:
                start=vis_data['fnum']
            end=vis_data['fnum']
    return start,end


def enhance(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    c=1
    hsv[:,:,c]=np.clip(hsv[:,:,c].astype('int16')+15,0,255).astype('uint8')
    #hsv[:,:,1]+=70
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

if __name__=='__main__':
    print('nosync',args.nosync)
    if not args.novid:
        reader = gst_file_reader(args.path,nosync = args.nosync)
    #fd = open(args.path+'/data.pkl','rb')

    start_frame,end_frame = get_first_and_last(args.path+'/viewer_data.pkl')
    print('start_frame,end_frame',start_frame,end_frame)

    if os.path.isfile(args.path+'/data.pkl'):
        fd = open(args.path+'/data.pkl','rb')
        print('reading data.pkl')
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
    save_avi = None

    track = None
    lock = False

    while 1:
        hist_buff_ind=fcnt%len(imbuff)
        if not args.novid and imbuff[hist_buff_ind]!=None and imbuff[hist_buff_ind][0]==fcnt:
            fcnt,images,vis_data,main_data=imbuff[hist_buff_ind]
            from_buff=True
        else:
            if not args.novid:
                images,fcnt=reader.__next__()
                #if images is not None:
                #    images=(images[0][:,:,::-1].copy(),images[1][:,:,::-1].copy())
            else:
                fcnt+=1
                images=[None,None]
            from_buff=False
            #print('fnum in image',fcnt)
            while fcnt>-1:
                try:
                    ret=pickle.load(fd)
                except EOFError:
                    print('No more data')
                    if args.novid:
                        explore.plot_graphs(main_data_hist,vis_data_hist)
                        sys.exit(0)
                    break
                if args.pub_data:
                    if type(ret[0])==bytes:
                        socket_pub.send_multipart([ret[0],pickle.dumps(ret[1])])
                #print('topic=',ret[0])
                if ret[0]==config.topic_comp_vis:
                    vis_data=ret[1]
                    #print('fnum in vis',vis_data['fnum'])
                    vis_data_hist.append(vis_data)
                    if len(vis_data_hist)>args.bs:
                        vis_data_hist.pop(0)
                    if vis_data['fnum']>=fcnt:
                        break
                if ret[0]==config.topic_mav_telem:
                    #data=pickle.loads(ret[1])
                    data=ret[1]
                    #'mavpackettype': 'VFR_HUD'
                    #print('---',data['mavpackettype'])
                    #print('---',data)
                    if data['mavpackettype'] in { 'VFR_HUD' , 'SERVO_OUTPUT_RAW' ,'ATTITUDE'}:
                        #print('mav telem',data)
                        if 'VFR_HUD' == data['mavpackettype']:
                            main_data.update({
                                'depth':abs(data['alt']),
                                'heading':data['heading'],
                                'climb':data['climb'],
                                })
                        if 'ATTITUDE' == data['mavpackettype']:
                            main_data.update(data)
                            #print('-----  ',data)
                            #try:
                            #    print('-----  ',data['yaw']*180/np.pi,main_data['heading'])
                            #except:
                            pass
                if ret[0]==config.topic_main_telem:
                    #main_data.update(pickle.loads(ret[1]))
                    main_data.update(ret[1])
                    main_data_hist.append(main_data.copy())
                    #if 'mavpackettype' not in data:
                    if len(main_data_hist)>args.bs:
                        main_data_hist=main_data_hist[1:]
                    #    print(data)
                if ret[0]==config.topic_button:
                    print('got bottons',ret[1])
            if not args.novid and fcnt>0:
                hist_buff_ind=fcnt%len(imbuff)
                imbuff[hist_buff_ind]=(fcnt,images,vis_data,main_data)

        imgs_raw=[None,None]
        if fcnt >0 and images[0] is not None and images[1] is not None:
            #if 1 or not  from_buff:
            for i in [0,1]:
                if not args.nosingle and args.nowait <= fcnt:
                    for ext in ['.ppm','.png','.webp','.pgm']:
                        fname=file_path_fmt.format('lr'[i],fcnt)+ext
                        if os.path.isfile(fname):
                            try:
                                frame=cv2.imread(fname)
                                if ext=='.pgm':
                                    frame=cv2.cvtColor(frame[:,:,0].copy(), cv2.COLOR_BAYER_BG2RGB_EA)[:,:,::-1]
                                if args.cc is not None:
                                    frame=apply_colorcc(frame)
                                imgs_raw[i]=frame
                                images[i]=imgs_raw[i][::2,::2,:].copy()
                            except Exception:
                                print('Failed read frame',fname)
                                traceback.print_exc(file=sys.stdout)
                            break

                    #images[i]=cv2.imread(fname)[:,:,::-1].copy()
                if imgs_raw[i] is None:
                    imgs_raw[i]=images[i].copy()#[:,:,::-1].copy()
                imgs_raw[i]=imgs_raw[i][:,:,::-1]
            if args.pub_images:
                socket_pub.send_multipart([\
                config.viewer_pub_image_topic,\
                pickle.dumps((imgs_raw[0][:,:,1],imgs_raw[1][:,:,1]))])

            if args.runtracker:
                if track is None:
                    #track = tracker.run_Trackers()
                    #track.__next__()
                    track = tracker.StereoTrack()
                else:
                    tic=time.time()
                    #ret=track.send((images[0],images[1],'lock' if lock else None))
                    #track.debug=True
                    ret=track(images[0],images[1])
                    if lock:
                        lock=False
                    toc=time.time()
                    print('run track took {} {:4.1f} msec'.format(fcnt,(toc-tic)*1000))
                    images_copy=(images[0].copy(),images[1].copy())
                    tracker.draw_track_rects(ret,images_copy[0],images_copy[1])
                    join[:,0:sx,:]=images_copy[0]
                    join[:,sx:,:]=images_copy[1]

            else:
                tracker.draw_track_rects(vis_data,images[0],images[1])
                join[:,0:sx,:]=images[0]
                join[:,sx:,:]=images[1]

            draw_txt(join,vis_data,main_data)
            if explore.is_data_file(args.path,fcnt):
                cv2.circle(join,(0,0), 15, (0,0,255), -1)

            if save_avi is not None:
                save_avi.write(join)

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(join,'Play {:.1f} tot {:.1f} sec'.format((fcnt-start_frame)/10 ,(end_frame-start_frame)/10)
                ,(2,12), font, 0.4,(255,0,255),1,cv2.LINE_AA)

            cv2.imshow('3dviewer '+base_name,join)
            #cv2.imshow('left',images[0])
            #cv2.imshow('right',images[1])
        if args.nowait > fcnt:
            k=cv2.waitKey(1)
            if images is not None:
                fcnt+=1
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
        if k%256==ord(' '):
            fcnt+=1
        if k%258==ord('x'):
            cv2.imwrite('out{:08d}.png'.format(fcnt),join)
        if k%256==ord('s'):
            #import pdb;pdb.set_trace()
            save_sy,save_sx=images[0].shape[:2]
            save_sx*=2
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            #fourcc = cv2.VideoWriter_fourcc(
            save_avi = cv2.VideoWriter('./output.avi', fourcc , 20.0, (save_sx,save_sy))
        if k%256==ord('t'):
            track.debug=fcnt
    if save_avi is not None:
        save_avi.release()
        print('to convert to webm run:')
        print('ffmpeg -i output.avi -cpu-used 2 -b:v 1M output.webm')


### fmt_cnt_l,imgl,imgr=imgget.__next__()
###                fmt_cnt_r=fmt_cnt_l
###                img=imgl
