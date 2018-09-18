# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import argparse,sys,os,time
from datetime import datetime
sys.path.append('../')
import zmq
import struct
import cv2,os
import numpy as np
import pickle
import select

import tracker
import gst
import config
import utils

parser = argparse.ArgumentParser()
parser.add_argument("--cvshow",help="show opencv mode", action='store_true')
parser.add_argument("--data_path", help="path for data")
parser.add_argument("--save",help="save data", action='store_true')
parser.add_argument("--gst",help="stream with gst", action='store_true')
args = parser.parse_args()

###############params configs

def get_disk_usage():
    return os.popen("df -h / |tail -1 | gawk '{print $5}'").read()

save=0
if args.save:
    #if not os.path.isdir(args.data_path):
    if not os.path.isdir('../data'):
        os.mkdir('../data')

topicl=config.topic_unreal_drone_rgb_camera%0+b'l'
topicr=config.topic_unreal_drone_rgb_camera%0+b'r'

subs_socks=[]
subs_socks.append( utils.subscribe([ topicl,topicr ],config.zmq_pub_unreal_proxy))
subs_socks.append( utils.subscribe([ config.topic_button,config.topic_axes ],config.zmq_pub_joy))
subs_socks.append( utils.subscribe([ config.topic_imu ],config.zmq_pub_imu) )
subs_socks.append( utils.subscribe([ config.topic_main_telem, config.topic_mav_telem ],config.zmq_pub_main) )


socket_pub = utils.publisher(config.zmq_pub_comp_vis)



image_fmt='ppm'

print('start...')
start=time.time()

#stereo = cv2.StereoBM_create(numDisparities=64, blockSize=5)
stereo = cv2.StereoSGBM_create(numDisparities=64*2, blockSize=9)

debug=False

def shrink(img):
    return ((img[::2,::2,:].astype('uint16')+
            img[1::2,::2,:]+
            img[1::2,1::2,:]+
            img[::2,1::2,:])//4).astype('uint8')


def listener():
    global debug,gst_pipes,save
    record_state=False
    fmt_cnt_l=-1
    fmt_cnt_r=-2
    keep_running=True
    track=None
    
    last_usage_test=time.time()
    disk_usage=get_disk_usage()
    fd=None

    #send initial trigger
    print('start trig')
    socket_pub.send_multipart([config.topic_comp_vis_cmd,b'start_trig'])

    while keep_running:
        socks=zmq.select(subs_socks,[],[],0.001)[0]
        for sock in socks:
            ret=sock.recv_multipart() 
            if ret[0]==config.topic_button:
                data=pickle.loads(ret[1])
                if data[config.joy_init_track]==1:
                    print('init tracker')
                    track = tracker.run_Trackers()
                    track.__next__()
                if data[config.joy_save]==1 and args.save:
                    record_state = not record_state
                    print('recording ',record_state)
                    if record_state:
                        save = '../data/'+datetime.now().strftime('%y%m%d-%H%M%S')
                        os.mkdir(save)
                        data_fd=open(save+'/data.pkl','wb')
            
            if record_state and ret[0] not in [topicl,topicr]:
                #save only data not images
                pickle.dump(ret,data_fd,-1)

            if ret[0] in [topicl,topicr]:
                topic, info, data = ret
                info=struct.unpack('llll',info)
                shape=info[:3]
                if topic==topicl:
                    fmt_cnt_l=info[3]
                    imgl=data
                if topic==topicr:
                    fmt_cnt_r=info[3] 
                    imgr=data

            if ret[0] in [topicl,topicr] and fmt_cnt_r == fmt_cnt_l:
                imgl=np.fromstring(imgl,'uint8').reshape(shape)
                imgr=np.fromstring(imgr,'uint8').reshape(shape)
                if save and record_state and (info[3]%10==0): #save every 1 sec
                    cv2.imwrite(save+'/l{:08d}.{}'.format(info[3],image_fmt),imgl)
                    cv2.imwrite(save+'/r{:08d}.{}'.format(info[3],image_fmt),imgr)
                if time.time()-last_usage_test>10.0:
                    last_usage_test=time.time()
                    disk_usage=get_disk_usage()
                
                #### shrink images if needed  
                if shape[1] > 640:
                    img=imgl=shrink(imgl)
                    imgr=shrink(imgr)
                else:
                    img=imgl
                
                ###################################################################### 
                wx,wy=config.stereo_corr_params['ws']
                cx = img.shape[1]//2
                cy = img.shape[0]//2
                draw_rectsr=[((cx-wx//2,cy-wy//2) , (cx+wx//2,cy+wy//2) , (0,255,255))]
                draw_rectsl=[((cx-wx//2,cy-wy//2) , (cx+wx//2,cy+wy//2) , (0,0,255))]
                if track is None:
                    track = tracker.run_Trackers()
                    track.__next__()
                else:
                    tic=time.time()
                    ret=track.send((imgl,imgr,None))
                    toc=time.time()
                    ret['ts']=toc 
                    ret['draw_rectsl']=draw_rectsl
                    ret['draw_rectsr']=draw_rectsr
                    ret['record_state']=record_state
                    ret['disk_usage']=disk_usage
                    ret['fnum']=fmt_cnt_l

                    ox=int(ret['disp'])                    
                    draw_rectsr.append(((cx-wx//2+ox,cy-wy//2) , (cx+wx//2+ox,cy+wy//2) , (0,0,255)))
                    ox,oy=int(ret['offx']),int(ret['offy'])
                    draw_rectsl.append(((cx-wx//2+ox,cy-wy//2+oy) , (cx+wx//2+ox,cy+wy//2+oy) , (255,0,255)))
                    socket_pub.send_multipart([config.topic_comp_vis,pickle.dumps(ret,-1)])
                    if record_state:
                        pickle.dump([config.topic_comp_vis,ret],data_fd,-1)

                    pline = 'F{:06} SNR{:5.2f} RG{:5.2f} OF {:3.2f},{:3.2f},     ftime {:3.3f}ms'.\
                            format(fmt_cnt_l,ret['snr_corr'],ret['range'],ret['offx'],ret['offy'],(toc-tic)*1000)
                    if 'dx' in ret:
                        pline+=' DX{:5.3f} DY{:5.3f}'.format(ret['dx'],ret['dy'])

                ######################################################################
                if  args.gst:
                    if gst.gst_pipes is None:
                        gst.init_gst(img.shape[1],img.shape[0],2)
                    gst.send_gst([imgl,imgr])

                ######################################################################
                if args.cvshow:
                    show_imager=imgr.copy()
                    show_imagel=imgl.copy()
                    for rectp in draw_rectsr:
                        cv2.rectangle(show_imager,*rectp)
                    cv2.imshow('imgr',show_imager)
                    for rectp in draw_rectsl:
                        cv2.rectangle(show_imagel,*rectp)
                    cv2.imshow('imgl',show_imagel)
                    k=cv2.waitKey(1)
                    if k==ord('q'):
                        keep_running = False
                        plot.send('stop')
                        break
                    if k==ord('d'):
                        tracker.debug=True
                    if k==ord('l'): #lock
                        track=None

       
if __name__ == '__main__':
    listener()
