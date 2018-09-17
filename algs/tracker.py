# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import polyfit
import config
import cv2
import scipy
import scipy.signal

track_params = config.track_params 
stereo_corr_params = config.stereo_corr_params
debug=False

def disp2range(x):
    if x==0:
        x=0.01 #avoid devision by 0
    return -config.baseline*config.focal_length/x

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
        #corr_pat=preprep_corr(patern)
        corr_pat=patern.copy()

        img2=img
        while True:
            l2,r2=cx-wx//2-sx,cx+wx//2+sx
            u2,d2=cy-wy//2-sy,cy+wy//2+sy
            search=img2[u2:d2,l2:r2]
            #corr_search=preprep_corr(search)
            corr_search=search.copy()
            #corr=scipy.signal.correlate2d(corr_search, corr_pat, mode='valid', boundary='fill', fillvalue=0)
            #corr = scipy.signal.convolve2d(corr,np.ones((3,3)),'same')
    
            corr = cv2.matchTemplate(corr_search,corr_pat,cv2.TM_CCOEFF_NORMED)    
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr)
            x,y = max_loc
            if 1<=x<corr.shape[1]-1 and 1<=y<corr.shape[0]-1:
                dx,dy=polyfit.fit(corr[y-1:y+2,x-1:x+2])
                x+=dx
                y+=dy
            #y, x = np.unravel_index(np.argmax(corr), corr.shape)
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
    #corr_pat=preprep_corr(patern)
    corr_pat=patern.copy()

    #patern=np.log(patern)
    #search=img2[cy-sy//2:cy+sy//2,cx-sx//2:cx+sx//2].copy()
    l2,r2=cx-wx//2-sxl,cx+wx//2+sxr
    #search up and down incase of inacurate camera model
    sy=12
    u2,d2=cy-wy//2-sy,cy+wy//2+sy
    search=img2[u2:d2,l2:r2]
    #corr_search=preprep_corr(search)
    corr_search=search.copy()
    
    #search_zoom=scipy.ndimage.zoom(search, 4, order=3)
    #search=np.log(search)
    #corr=scipy.signal.correlate2d(patern, search, mode='valid', boundary='fill', fillvalue=0)
    #corr = scipy.signal.convolve2d(corr,np.ones((3,3)),'same')
    #y, x = np.unravel_index(np.argmax(corr), corr.shape) 
    
    corr = cv2.matchTemplate(corr_search,corr_pat,cv2.TM_CCOEFF_NORMED)    
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr)
    x,y = max_loc
    #################zoom
    #import ipdb;ipdb.set_trace()
    if 1<=x<corr.shape[1]-1 and 1<=y<corr.shape[0]-1:
        dx,dy=polyfit.fit(corr[y-1:y+2,x-1:x+2])
        x+=dx
        y+=dy
        #:print(x,y)  

    nx=x-sxl
    if 0 and x>sz:
        z=4
        sz=3 #zoom search
        lz1,rz1=wx//2-(wx//2)//z,wx//2+(wx//2)//z
        uz,dz=wx//2-(wx//2)//z,wx//2+(wx//2)//z
        patern_zoom=corr_pat[uz:dz,lz1:rz1]
        patern_zoom=scipy.ndimage.zoom(patern_zoom, z, order=3)
        lz2,rz2=x+wx//2-(wx//2)//z-sz,x+wx//2+(wx//2)//z+sz
        search_zoom=corr_search[uz:dz,lz2:rz2]
        search_zoom=scipy.ndimage.zoom(search_zoom, z, order=3)
        corrz=scipy.signal.correlate2d(search_zoom, patern_zoom, mode='valid', boundary='fill', fillvalue=0)
        zy, zx = np.unravel_index(np.argmax(corrz), corrz.shape)         
        nx=x-sxl-sz+zx/z

    ##########################
    
    #avg_corr=corr[y-1:y+1,x-1:x+1].mean()
    #corr[y-1:y+1,x-1:x+1]=-9999999
    #max_rest=np.ma.masked_array(corr,corr==-9999999).max()
    
    offx = x
    offy = y
    snr = 10*np.log10((corr.max()/np.median(corr))**2) 
    #snr = 10*np.log10(max_val) 
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

            if 0:
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

def run_Trackers():
    print('-------------------- init trackers -------------')
    tc = None
    imgl,imgr,cmd = yield
    imgl1b=imgl[:,:,2].copy()
    imgr1b=imgr[:,:,2].copy()
    imgl1r=imgl[:,:,0].copy()
    imgr1r=imgr[:,:,0].copy()
    tc=track_correlator(imgl1b,*track_params)
    tc.__next__()
    sp = stereo_corr_params
    range_win=[]

    while True:
        res={}
        res['img_shp']=imgl.shape
        res['line_corr_parr']=stereo_corr_params
        cret = line_correlator(imgl1r,imgr1r,sp['ws'][0],sp['ws'][1],sp['sxl'],sp['sxr'])
        ox,oy = tc.send(imgl1b)
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
            dx = res['range_avg'] * ox/config.focal_length
            dy = res['range_avg'] * oy/config.focal_length
            res['dx']=dx
            res['dy']=dy
        else:
            tc=track_correlator(imgl1b,*track_params)
            tc.__next__()
            

        imgl,imgr,cmd = yield res 
        imgl1b=imgl[:,:,2].copy()
        imgr1b=imgr[:,:,2].copy()
        imgl1r=imgl[:,:,0].copy()
        imgr1r=imgr[:,:,0].copy()
        if cmd=='lock':
            tc=track_correlator(imgl1b,*track_params)
            tc.__next__()


