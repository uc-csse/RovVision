# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import sys,os,time
sys.path.append('../../DroneSimLab/demos/bluerov/unreal_proxy')
import zmq
import struct
import cv2,os
import numpy as np
import config
from subprocess import Popen,PIPE

doplot=1
if doplot:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

save=0
save='/tmp/tst1'

if save:
    ret=os.mkdir(save)
    print(ret)

context = zmq.Context()
zmq_sub = context.socket(zmq.SUB)
addr="tcp://%s:%d" % (config.zmq_pub_unreal_proxy)
zmq_sub.connect(addr)
#topicm=config.topic_unreal_drone_rgb_camera%0
topicl=config.topic_unreal_drone_rgb_camera%0+b'l'
topicr=config.topic_unreal_drone_rgb_camera%0+b'r'
#zmq_sub.setsockopt(zmq.SUBSCRIBE,topicm)
zmq_sub.setsockopt(zmq.SUBSCRIBE,topicl)
zmq_sub.setsockopt(zmq.SUBSCRIBE,topicr)
#zmq_sub.setsockopt(zmq.SUBSCRIBE,topic+b'down') 
#zmq_sub.setsockopt(zmq.SUBSCRIBE,topic+b'depth') 
cvshow=1
#cvshow=False

print('start...')
start=time.time()

#stereo = cv2.StereoBM_create(numDisparities=64, blockSize=5)
stereo = cv2.StereoSGBM_create(numDisparities=64*2, blockSize=9)

#camera info estimate
fov=90.0
pixelwidth = 640 #after shrink
baseline = 0.2 # ~20cm
focal_length=pixelwidth/( np.tan(np.deg2rad(fov/2)) *2 )
#disparity=x-x'=baseline*focal_length/Z
#=>> Z = baseline*focal_length/disparity 

def disp2range(x):
    return baseline*focal_length/x

def avg_disp_win(disp,centx,centy,wx,wy,tresh,min_dis=50):
    win=disp[centy-wy//2:centy+wy//2,centx-wx//2:centx+wx//2]
    winf=win.flatten()
    winf=winf[winf>min_dis]
    if len(winf)>tresh:
        #hist,bins=np.histogram(winf,20)
        #b=hist.argmax()
        #val=(bins[b]+bins[b+1])/2
        return winf.mean(),winf.max(),winf.min(),len(winf)
    return -1,-1,-1,-1


def preisterproc(img):
    h=img.shape[0]
    img_shrk = img[h//4:h-h//4,:] 
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #return gray
    return img_shrk

lmap = lambda func, *iterable: list(map(func, *iterable))


def ploter():
    fig = plt.figure(figsize=(8,6))
    ax1 = fig.add_subplot(4, 1, 1)
    ax1.set_title('disp')
    ax2 = fig.add_subplot(4, 1, 2)
    ax2.set_title('-')
    ax3 = fig.add_subplot(4, 1, 3)
    ax3.set_title('-')
    ax4 = fig.add_subplot(4, 1, 4)
    ax4.set_title('-')
    ax4.set_ylim(-1,1)
    fig.canvas.draw()   # note that the first draw comes before setting data 
    #fig.canvas.mpl_connect('close_event', handle_close)
    #h1 = ax1.plot([0,1],[0,1],[0,1], lw=3)[0]
    #text = ax1.text(0.8,1.5, '')
    t_start = time.time()
    history=[]

    cnt=0
    mem_len=200
    hdl_list=[]
    alt_ref=None
    last_plot=time.time()
    while True:
        cnt+=1
        data=yield
        if data=='stop':
            break
        history=history[-mem_len:]
        history.append(data) 

        if time.time()-last_plot<0.2 and cnt%10!=0:
            continue        
        last_plot=time.time()

        for hdl in hdl_list:
            hdl[0].remove()
        hdl_list=[]
        
        disp=np.array(lmap(lambda x:x['disp'],history))
        ts=np.array(lmap(lambda x:x['tstemp'],history))

        hdl_list.append(ax1.plot(ts,disp,'-b',alpha=0.5)) 
        ax1.set_xlim(ts.min(),ts.max())        
        #if cnt<100:        
        fig.canvas.draw()
        w=plt.waitforbuttonpress(timeout=0.001)
        if w==True: #returns None if no press
            disp('Button click')
            break
 


def listener():
    fmt_cnt_l=-1
    fmt_cnt_r=-2
    if doplot:
        plot=ploter()
        plot.__next__()
    keep_running=True
    while keep_running:
        while len(zmq.select([zmq_sub],[],[],0.001)[0])>0:
            topic, info, data = zmq_sub.recv_multipart()
            #topic=topic.decode()
            info=struct.unpack('llll',info)
            shape=info[:3]
            img=np.fromstring(data,'uint8').reshape(shape)
            if topic==topicl:
                fmt_cnt_l=info[3]
                imgl=img
            if topic==topicr:
                fmt_cnt_r=info[3] 
                imgr=img

            if save:
                cv2.imwrite(save+'/{}{:08d}.png'.format('l' if topic==topicl else 'r',info[3]),img)

            if cvshow:
                #if 'depth' in topic:
                #    cv2.imshow(topic,img)
                #else:
                #cv2.imshow(topic,cv2.resize(cv2.resize(img,(1920/2,1080/2)),(512,512)))
                img_shrk = img[::2,::2]

                centx=None
                centy=None
                wx=100
                wy=100

                if fmt_cnt_r == fmt_cnt_l:
                    disparity = stereo.compute(preisterproc(imgl),preisterproc(imgr))
                    disparityu8 = np.clip(disparity,0,255).astype('uint8')

                    centx=disparityu8.shape[1]//2
                    centy=disparityu8.shape[0]//2
                    #print('--->',disparity.max(),disparity.min(),type(disparity),imgr.shape)
                    #disparityu8[centy-wy//2:centy+wy//2,centx-wx//2:centx+wx//2]=255
                    cv2.rectangle(disparityu8, (centx-wx//2,centy-wy//2) , (centx+wx//2,centy+wy//2) , 255)
                    cv2.imshow('disparity',disparityu8)
                    avg_disp,min_d,max_d,cnt_d=avg_disp_win(disparity,centx,centy,wx,wy,tresh=10)
                    print('D {:05.2f}, {:05.2f} ,{:05.2f} ,{:05d} R {:5.2f}'.format(avg_disp,min_d,max_d,cnt_d,disp2range(avg_disp)))
                    if doplot:
                        plot.send({'tstemp':time.time()-start,'disp':avg_disp})
                centx_full = img.shape[1]//2
                centy_full = img.shape[0]//2
                cv2.rectangle(img, (centx_full-wx//2,centy_full-wy//2) , (centx_full+wx//2,centy_full+wy//2) , (0,0,255))
                cv2.imshow(topic.decode(),img)

                    #import pdb;pdb.set_trace()
                k=cv2.waitKey(1)
                if k==ord('q'):
                    keep_running = False
                    plot.send('stop')
                    break

            ### test
        time.sleep(0.010)


       
if __name__ == '__main__':
    listener()
