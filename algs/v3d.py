# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import argparse,sys,os,time
sys.path.append('../')
import zmq
import struct
import cv2,os
import numpy as np
import scipy
import scipy.signal
import pickle

parser = argparse.ArgumentParser()
#parser.add_argument("-f","--dump_file_prefix", help="dump_file prefix name will create two file one for video and one for data")
parser.add_argument("-o","--overide", help="allow overide of dump file", action='store_true')
#parser.add_argument("-s","--show",help="open opencv video",action='store_true')
#parser.add_argument("-c","--cvstream",help="stream video to local port 9345", action='store_true')
#parser.add_argument("-d","--dronesimlab",help="simulation mode", action='store_true')
parser.add_argument("--cvshow",help="show opencv mode", action='store_true')
parser.add_argument("--data_path", help="path for data")
parser.add_argument("--save",help="save data", action='store_true')
parser.add_argument("--doplot",help="plot data", action='store_true')
parser.add_argument("--gst",help="stream with gst", action='store_true')
parser.add_argument("--calc_disparity",help="calc disparity", action='store_true')
args = parser.parse_args()

import config
###############params configs

from subprocess import Popen,PIPE

doplot=args.doplot
if doplot:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D


save=0
if args.save:
    if os.path.isdir(args.data_path) and not args.overide:
        print('Error data path exist use -o to override')
        sys.exit(-1)
    ret=os.mkdir(args.data_path)
    save=args.data_path
    #print(ret)

if not save and 'data_path' in args:
    load=args.data_path
else:
    load=0
    import config

############# gst ########
#to watch
#gst-launch-1.0 -e -v udpsrc port=5700 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
#gst-launch-1.0 -e -v udpsrc port=5701 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
gst_pipes=None
def init_gst(sx,sy,npipes):
    global gst_pipes
    #cmd="gst-launch-1.0 {}! x264enc tune=zerolatency  bitrate=500 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
    if 0: #h264 stream
        cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=500 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
        gstsrc = 'fdsrc ! videoparse width={} height={} framerate=30/1 format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
    
    cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=500 key-int-max=30 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
    gstsrc = 'fdsrc ! videoparse width={} height={} framerate=30/1 format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'

    gst_pipes=[]
    for i in range(npipes):
        gcmd = cmd.format(gstsrc,5700+i)
        p = Popen(gcmd, shell=True, bufsize=1024*10,stdin=PIPE, stdout=sys.stdout, close_fds=False)
        gst_pipes.append(p)

def send_gst(imgs):
    global gst_pipes
    for i,im in enumerate(imgs):
        time.sleep(0.001)
        gst_pipes[i].stdin.write(im.tostring())
    
#############################


context = zmq.Context()

if not load:
    print('subscribing')
    zmq_sub = context.socket(zmq.SUB)
    addr="tcp://%s:%d" % (config.zmq_pub_unreal_proxy)
    zmq_sub.connect(addr)
    #topicm=config.topic_unreal_drone_rgb_camera%0
    topicl=config.topic_unreal_drone_rgb_camera%0+b'l'
    topicr=config.topic_unreal_drone_rgb_camera%0+b'r'
    #zmq_sub.setsockopt(zmq.SUBSCRIBE,topicm)
    zmq_sub.setsockopt(zmq.SUBSCRIBE,topicl)
    zmq_sub.setsockopt(zmq.SUBSCRIBE,topicr)

    zmq_sub_joy = context.socket(zmq.SUB)
    zmq_sub_joy.connect("tcp://127.0.0.1:%d" % config.zmq_pub_joy)
    zmq_sub_joy.setsockopt(zmq.SUBSCRIBE,config.topic_button)


socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://127.0.0.1:%d" % config.zmq_pub_comp_vis )

#socket_pub_imgs = context.socket(zmq.PUB)
#socket_pub.bind("tcp://127.0.0.1:%d" % config.zmq_pub_comp_vis_imgs )

image_fmt='jpg'

if load:
    def imggetter():
        import glob,re
        #image_fmt='webp'
        #lefts=glob.glob(load+'/l*.png')
        lefts=glob.glob(load+'/l*.'+image_fmt)
        lefts.sort()
        rights=glob.glob(load+'/r*.'+image_fmt)
        rights.sort()
        for l,r in zip(lefts,rights):
            fnum = int(re.findall('0[0-9]+',l)[0])
            yield fnum,cv2.imread(l),cv2.imread(r)


    imgget=imggetter()
print('start...')
start=time.time()

#stereo = cv2.StereoBM_create(numDisparities=64, blockSize=5)
stereo = cv2.StereoSGBM_create(numDisparities=64*2, blockSize=9)

#camera info estimate
fov=60.97
pixelwidthx = 640 #after shrink
pixelwidthy = 512 #after shrink
baseline = 0.14 # (240-100)*.1scale in cm from unreal engine
focal_length=pixelwidthx/( np.tan(np.deg2rad(fov/2)) *2 )
#disparity=x-x'=baseline*focal_length/Z
#=>> Z = baseline*focal_length/disparity 
track_params = (30,30,20,20) 
stereo_corr_params = {'ws':(100,100),'sxl':0,'sxr':500}

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

debug=False

def preprep_corr(img):
    ret=np.log(img.astype('float')+1)
    #ret=img.astype('float')
    ret-=ret.mean()
    ret/=ret.max()
    return ret


def track_correlator(img,wx,wy,sx,sy,tx=None,ty=None):
    if tx is None:
        tx=sx//2
    if ty is None:
        ty=sy//2

    while True: 
        cx=img.shape[1]//2
        cy=img.shape[0]//2
        l1,r1=cx-wx//2,cx+wx//2
        u1,d1=cy-wy//2,cy+wy//2
        patern=img[u1:d1,l1:r1]
        corr_pat=preprep_corr(patern)

        img2=img
        while True:
            l2,r2=cx-wx//2-sx,cx+wx//2+sx
            u2,d2=cy-wy//2-sy,cy+wy//2+sy
            search=img2[u2:d2,l2:r2]
            corr_search=preprep_corr(search)
            corr=scipy.signal.correlate2d(corr_search, corr_pat, mode='valid', boundary='fill', fillvalue=0)
            corr = scipy.signal.convolve2d(corr,np.ones((3,3)),'same')
            y, x = np.unravel_index(np.argmax(corr), corr.shape)
            ox,oy = x-sx,y-sy
            if abs(ox)>tx or abs(oy)>ty : #new reference if translate to much
                img=yield ox,oy
                break
            img2=yield ox,oy


def line_correlator(img1,img2,wx,wy,sxl,sxr):
    global debug
    cx=img1.shape[1]//2
    cy=img1.shape[0]//2
    l1,r1=cx-wx//2,cx+wx//2
    u1,d1=cy-wy//2,cy+wy//2
    patern=img1[u1:d1,l1:r1]
    corr_pat=preprep_corr(patern)

    #patern=np.log(patern)
    #search=img2[cy-sy//2:cy+sy//2,cx-sx//2:cx+sx//2].copy()
    l2,r2=cx-wx//2-sxl//2,cx+wx//2+sxr//2
    u2,d2=cy-wy//2,cy+wy//2
    search=img2[u2:d2,l2:r2]
    corr_search=preprep_corr(search)
    #search_zoom=scipy.ndimage.zoom(search, 4, order=3)
    #search=np.log(search)
    #corr=scipy.signal.correlate2d(patern, search, mode='valid', boundary='fill', fillvalue=0)
    corr=scipy.signal.correlate2d(corr_search, corr_pat, mode='valid', boundary='fill', fillvalue=0)
    corr = scipy.signal.convolve2d(corr,np.ones((3,3)),'same')
    y, x = np.unravel_index(np.argmax(corr), corr.shape) 
    
    #################zoom
    z=4
    sz=3 #zoom search
    lz1,rz1=wx//2-(wx//2)//z,wx//2+(wx//2)//z
    uz,dz=wx//2-(wx//2)//z,wx//2+(wx//2)//z
    patern_zoom=corr_pat[uz:dz,lz1:rz1]
    patern_zoom=scipy.ndimage.zoom(patern_zoom, z, order=3)

    nx=x
    if x>sz:
        lz2,rz2=x+wx//2-(wx//2)//z-sz,x+wx//2+(wx//2)//z+sz
        search_zoom=corr_search[uz:dz,lz2:rz2]
        search_zoom=scipy.ndimage.zoom(search_zoom, z, order=3)
        corrz=scipy.signal.correlate2d(search_zoom, patern_zoom, mode='valid', boundary='fill', fillvalue=0)
        zy, zx = np.unravel_index(np.argmax(corrz), corrz.shape)         
        nx=x-sz+zx/z

    ##########################
    
    #avg_corr=corr[y-1:y+1,x-1:x+1].mean()
    #corr[y-1:y+1,x-1:x+1]=-9999999
    #max_rest=np.ma.masked_array(corr,corr==-9999999).max()
    
    offx = x
    offy = y
    snr = 10*np.log10((corr.max()/np.median(corr))**2) 
    #print('===',corr[y,x])
    if debug:
        if 1:
            import matplotlib.pyplot as plt
            plt.figure('search')
            plt.subplot(3,1,1)
            plt.imshow(patern)
            plt.subplot(3,1,2)
            plt.imshow(search)
            plt.subplot(3,1,3)
            l=len(corr[0,:])
            plt.plot(np.linspace(0,l,l),corr[0,:])
            c2=scipy.signal.resample(corr[0,:],l*4)
            plt.plot(np.linspace(0,l,len(c2)),c2)

            plt.figure('search_zoom')
            plt.subplot(3,1,1)
            plt.imshow(patern_zoom)
            plt.subplot(3,1,2)
            plt.imshow(search_zoom)
            plt.subplot(3,1,3)
            l=len(corr[0,:])
            plt.plot(corrz[0,:])
            #c2=scipy.signal.resample(corrz[0,:],l*4)
            #plt.plot(np.linspace(0,l,len(c2)),c2)

            
            plt.figure('img1/2 %.2f'%snr)
            ax1=plt.subplot(1,2,1)
            plt.imshow(img1)
            plt.plot([l1,r1,r1,l1,l1],[u1,u1,d1,d1,u1],'r')
            plt.subplot(1,2,2,sharex=ax1,sharey=ax1)
            plt.imshow(img2)
            plt.plot([l2,r2,r2,l2,l2],[u2,u2,d2,d2,u2],'b')
            xx=np.array([l2,l2+wx,l2+wx,l2,l2])+offx
            yy=np.array([u2,u2,u2+wy,u2+wy,u2])+offy
            plt.plot(xx,yy,'r')
            plt.show()
            import ipdb;ipdb.set_trace()
        debug=False
    #print('--->',x,nx,zx)
    return nx,snr






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
    ax2 = fig.add_subplot(4, 1, 2,sharex=ax1)
    ax2.set_title('corrx')
    ax3 = fig.add_subplot(4, 1, 3,sharex=ax1)
    ax3.set_title('snr corr')
    ax4 = fig.add_subplot(4, 1, 4,sharex=ax1)
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
        corrx=np.array(lmap(lambda x:x['corrx'],history))
        snr_corr=np.array(lmap(lambda x:x['snr_corr'],history))
        ts=np.array(lmap(lambda x:x['tstemp'],history))

        hdl_list.append(ax1.plot(ts,disp,'-b',alpha=0.5)) 
        hdl_list.append(ax2.plot(ts,corrx,'-b',alpha=0.5)) 
        hdl_list.append(ax3.plot(ts,snr_corr,'-b',alpha=0.5)) 
        ax1.set_xlim(ts.min(),ts.max())        
        #if cnt<100:        
        fig.canvas.draw()
        w=plt.waitforbuttonpress(timeout=0.001)
        if w==True: #returns None if no press
            disp('Button click')
            break
 



def run_Trackers():
    print('-------------------- init trackers -------------')
    tc = None
    imgl,imgr,cmd = yield
    tc=track_correlator(imgl[:,:,1],*track_params)
    tc.__next__()
    sp = stereo_corr_params
    range_win=[]

    while True:
        res={}
        res['img_shp']=imgl.shape
        res['line_corr_parr']=stereo_corr_params
        cret = line_correlator(imgl[:,:,1],imgr[:,:,1],sp['ws'][0],sp['ws'][1],sp['sxl'],sp['sxr'])
        ox,oy = tc.send(imgl[:,:,1])
        res['offx']=ox
        res['offy']=oy
        res['snr_corr']=cret[1]
        res['disp']=cret[0]
        res['range']=disp2range(cret[0])
        range_win.append(res['range'])
        if len(range_win) > 10:
            range_win=range_win[1:]
        if np.std(range_win)/np.mean(range_win)<0.10: #<5cm means reliable range
            res['range_avg']=np.mean(range_win)
            dx = res['range_avg'] * ox/focal_length
            dy = res['range_avg'] * oy/focal_length
            res['dx']=dx
            res['dy']=dy
        else:
            tc=track_correlator(imgl[:,:,1],*track_params)
            tc.__next__()
            

        imgl,imgr,cmd = yield res 
        if cmd=='lock':
            tc=track_correlator(imgl[:,:,1],*track_params)
            tc.__next__()


def listener():
    global debug,gst_pipes
    record_state=False
    fmt_cnt_l=-1
    fmt_cnt_r=-2
    if doplot:
        plot=ploter()
        plot.__next__()
    keep_running=True
    track=None
    while keep_running:

        if not load and zmq_sub_joy.poll(0):
        #if len(zmq.select([zmq_sub_joy],[],[],0.001)[0])>0 :
            ret  = zmq_sub_joy.recv_multipart()
            if ret[0]==config.topic_button:
                data=pickle.loads(ret[1])
                if data[5]==1:
                    print('init tracker')
                    track = run_Trackers()
                    track.__next__()
                if data[8]==1 and save:
                    record_state = not record_state
                    print('recording ',record_state)

        if load:
            frame_ready=True
            time.sleep(0.01)
        else:
            frame_ready= len(zmq.select([zmq_sub],[],[],0.001)[0])>0
        if frame_ready:
            if load:
                fmt_cnt_l,imgl,imgr=imgget.__next__()
                fmt_cnt_r=fmt_cnt_l
                img=imgl
                topic = b'load'
            else:
                ret  = zmq_sub.recv_multipart()
                topic, info, data = ret
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
                if save and record_state:
                    cv2.imwrite(save+'/{}{:08d}.{}'.format('l' if topic==topicl else 'r',info[3],image_fmt),img)

            wx,wy=stereo_corr_params['ws']
            if fmt_cnt_r == fmt_cnt_l:
                cx = img.shape[1]//2
                cy = img.shape[0]//2
                draw_rectsr=[((cx-wx//2,cy-wy//2) , (cx+wx//2,cy+wy//2) , (0,255,255))]
                draw_rectsl=[((cx-wx//2,cy-wy//2) , (cx+wx//2,cy+wy//2) , (0,0,255))]

                if track is None:
                    track = run_Trackers()
                    track.__next__()
                    #ox,oy=0,0
                else:
                    tic=time.time()
                    ret=track.send((imgl,imgr,None))
                    toc=time.time()
                    ret['ts']=toc 
                    ret['draw_rectsl']=draw_rectsl
                    ret['draw_rectsr']=draw_rectsr
                    ret['record_state']=record_state

                    ox=int(ret['disp'])                    
                    draw_rectsr.append(((cx-wx//2+ox,cy-wy//2) , (cx+wx//2+ox,cy+wy//2) , (0,0,255)))
                    ox,oy=ret['offx'],ret['offy']
                    draw_rectsl.append(((cx-wx//2+ox,cy-wy//2+oy) , (cx+wx//2+ox,cy+wy//2+oy) , (255,0,255)))

                    socket_pub.send_multipart([config.topic_comp_vis,pickle.dumps(ret,-1)])
                    pline = 'SNR{:5.2f} RG{:5.2f} OF {:03d},{:03d},     ftime {:3.3f}ms'.\
                            format(ret['snr_corr'],ret['range'],ret['offx'],ret['offy'],(toc-tic)*1000)
                    if 'dx' in ret:
                        pline+=' DX{:5.3f} DY{:5.3f}'.format(ret['dx'],ret['dy'])
                    print(pline)

                    #print('TC {:02d}, {:02d}'.format(ox,oy))
     

                    #if 'depth' in topic:
                    #    cv2.imshow(topic,img)
                    #else:
                    #cv2.imshow(topic,cv2.resize(cv2.resize(img,(1920/2,1080/2)),(512,512)))
                    #img_shrk = img[::2,::2]



                if args.gst:
                    if gst_pipes is None:
                        init_gst(img.shape[1],img.shape[0],2)
                    send_gst([imgl,imgr])

                if args.calc_disparity:
                    disparity = stereo.compute(preisterproc(imgl),preisterproc(imgr))
                    disparityu8 = np.clip(disparity,0,255).astype('uint8')

                    centx=disparityu8.shape[1]//2
                    centy=disparityu8.shape[0]//2
                #print('--->',disparity.max(),disparity.min(),type(disparity),imgr.shape)
                #disparityu8[centy-wy//2:centy+wy//2,centx-wx//2:centx+wx//2]=255
                #avg_disp,min_d,max_d,cnt_d=avg_disp_win(disparity,centx,centy,wx,wy,tresh=10)



                #    cret = correlator(imgl[:,:,1],imgr[:,:,1],wx,wy,sxl,sxr,syu,syd)
                #    print('D {:6.2f}, {:6.2f} ,{:6.2f} ,{:05d} R {:6.2f} C {:6.1f},{:6.1f} ,SC {:3.1f} R2 {:5.2f}'.\
                #            format(avg_disp,min_d,max_d,cnt_d,disp2range(avg_disp),cret[0],cret[1],cret[2],disp2range(cret[0])))
                if doplot:
                    plot.send({'tstemp':time.time()-start,'disp':avg_disp,'corrx':cret[0],'snr_corr':cret[2]})
                if args.cvshow:
                    if args.calc_disparity:
                        cv2.imshow('disparity',disparityu8)
                        cv2.rectangle(disparityu8, (centx-wx//2,centy-wy//2) , (centx+wx//2,centy+wy//2) , 255)
                    #img_toshow=img.copy()
                    show_imager=imgr.copy()
                    show_imagel=imgl.copy()
                    for rectp in draw_rectsr:
                        cv2.rectangle(show_imager,*rectp)
                    cv2.imshow('imgr',show_imager)
                    for rectp in draw_rectsl:
                        cv2.rectangle(show_imagel,*rectp)
                    cv2.imshow('imgl',show_imagel)

                        #import pdb;pdb.set_trace()
                    k=cv2.waitKey(0 if load else 1)
                    if k==ord('q'):
                        keep_running = False
                        plot.send('stop')
                        break
                    if k==ord('d'):
                        debug=True

                    if k==ord('l'): #lock
                        track=None
                        
            ### test


       
if __name__ == '__main__':
    listener()
