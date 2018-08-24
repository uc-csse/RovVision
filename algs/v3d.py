# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import sys,os,time
sys.path.append('../../DroneSimLab/demos/bluerov/unreal_proxy')
import zmq
import struct
import cv2,os
import numpy as np
import scipy
import scipy.signal

###############params
if not __name__=='__main__':
    save=0
    cvshow=0
    load=0
    doplot=0
else:
    save=0
    cvshow=1
    #save='/tmp/tst1'
    #load = '../data/tst1'
    #load = '/tmp/tst1'
    load = 0
    doplot=0

if not load:
    import config
from subprocess import Popen,PIPE

if doplot:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D



if save:
    ret=os.mkdir(save)
    print(ret)


if not load:
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

if load:
    def imggetter():
        import glob,re
        lefts=glob.glob(load+'/l*.png')
        lefts.sort()
        rights=glob.glob(load+'/r*.png')
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
pixelwidth = 640 #after shrink
baseline = 0.14 # (240-100)*.1scale in cm from unreal engine
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

debug=False
#correlator input img1 img2,search x left,search x right,search y up search y down
def correlator(img1,img2,wx,wy,sxl,sxr,syu,syd):
    global debug
    cx=img1.shape[1]//2
    cy=img1.shape[0]//2
    l1,r1=cx-wx//2,cx+wx//2
    u1,d1=cy-wy//2,cy+wy//2
    patern=img1[u1:d1,l1:r1]
    z=4
    #patern_zoom=scipy.ndimage.zoom(patern, 4, order=3)
    patern=np.log(patern.astype('float')+1)
    patern-=patern.mean()
    patern/=patern.max()
    #patern=np.log(patern)
    #search=img2[cy-sy//2:cy+sy//2,cx-sx//2:cx+sx//2].copy()
    l2,r2=cx-wx//2-sxl//2,cx+wx//2+sxr//2
    u2,d2=cy-wy//2-syu//2,cy+wy//2+syd//2
    search=img2[u2:d2,l2:r2]
    #search_zoom=scipy.ndimage.zoom(search, 4, order=3)
    search=np.log(search.astype('float')+1)
    search-=search.mean()
    search/=search.max()
    #search=np.log(search)
    #corr=scipy.signal.correlate2d(patern, search, mode='valid', boundary='fill', fillvalue=0)
    corr=scipy.signal.correlate2d(search, patern, mode='valid', boundary='fill', fillvalue=0)
    corr = scipy.signal.convolve2d(corr,np.ones((3,3)),'same')
    y, x = np.unravel_index(np.argmax(corr), corr.shape) 
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
            plt.figure('plots')
            plt.subplot(3,1,1)
            plt.imshow(patern)
            plt.subplot(3,1,2)
            plt.imshow(search)
            plt.subplot(3,1,3)
            if syu+syd>2:
                plt.imshow(corr,cmap='gray')
            else:
                l=len(corr[0,:])
                plt.plot(np.linspace(0,l,l),corr[0,:])
                c2=scipy.signal.resample(corr[0,:],l*4)
                plt.plot(np.linspace(0,l,len(c2)),c2)
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
    return x,y,snr

def preprep_corr(img):
    ret=np.log(img.astype('float')+1)
    ret-=ret.mean()
    ret/=ret.max()
    return ret

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
 


def listener():
    global debug
    fmt_cnt_l=-1
    fmt_cnt_r=-2
    if doplot:
        plot=ploter()
        plot.__next__()
    keep_running=True
    while keep_running:
        if load:
            frame_ready=True
        else:
            frame_ready= len(zmq.select([zmq_sub],[],[],0.001)[0])>0
        while frame_ready:
            if load:
                fmt_cnt_l,imgl,imgr=imgget.__next__()
                fmt_cnt_r=fmt_cnt_l
                img=imgl
                topic = b'load'
            else:
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
                sxl,sxr=20,500
                syu,syd=1,1

                if fmt_cnt_r == fmt_cnt_l:
                    disparity = stereo.compute(preisterproc(imgl),preisterproc(imgr))
                    disparityu8 = np.clip(disparity,0,255).astype('uint8')

                    centx=disparityu8.shape[1]//2
                    centy=disparityu8.shape[0]//2
                    #print('--->',disparity.max(),disparity.min(),type(disparity),imgr.shape)
                    #disparityu8[centy-wy//2:centy+wy//2,centx-wx//2:centx+wx//2]=255
                    cv2.imshow('disparity',disparityu8)
                    avg_disp,min_d,max_d,cnt_d=avg_disp_win(disparity,centx,centy,wx,wy,tresh=10)
                    if 1:
                        cret = line_correlator(imgl[:,:,1],imgr[:,:,1],wx,wy,sxl,sxr)
                        print('D {:6.2f}, {:6.2f} ,{:6.2f} ,{:05d} R {:6.2f} C {:6.1f},SC {:3.1f} R2 {:5.2f}'.\
                                format(avg_disp,min_d,max_d,cnt_d,disp2range(avg_disp),cret[0],cret[1],disp2range(cret[0])))
                    else:
                        cret = correlator(imgl[:,:,1],imgr[:,:,1],wx,wy,sxl,sxr,syu,syd)
                        print('D {:6.2f}, {:6.2f} ,{:6.2f} ,{:05d} R {:6.2f} C {:6.1f},{:6.1f} ,SC {:3.1f} R2 {:5.2f}'.\
                                format(avg_disp,min_d,max_d,cnt_d,disp2range(avg_disp),cret[0],cret[1],cret[2],disp2range(cret[0])))
                    if doplot:
                        plot.send({'tstemp':time.time()-start,'disp':avg_disp,'corrx':cret[0],'snr_corr':cret[2]})
                    cv2.rectangle(disparityu8, (centx-wx//2,centy-wy//2) , (centx+wx//2,centy+wy//2) , 255)
                centx_full = img.shape[1]//2
                centy_full = img.shape[0]//2
                img_toshow=img.copy()
                cv2.rectangle(img_toshow, (centx_full-wx//2,centy_full-wy//2) , (centx_full+wx//2,centy_full+wy//2) , (0,0,255))
                cv2.imshow(topic.decode(),img_toshow)

                    #import pdb;pdb.set_trace()
                k=cv2.waitKey(0 if load else 1)
                if k==ord('q'):
                    keep_running = False
                    plot.send('stop')
                    break
                if k==ord('d'):
                    debug=True

            ### test
        time.sleep(0.010)


       
if __name__ == '__main__':
    listener()