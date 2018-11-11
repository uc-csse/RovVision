# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import polyfit
import cv2
import scipy
import scipy.signal
import sys

import matplotlib
import matplotlib.pyplot as plt
sys.path.append("..")

import config
from utils import ab_filt

track_params = config.track_params 
stereo_corr_params = config.stereo_corr_params
from camera_tools import get_stereo_cameras,triangulate

def generate_stereo_cameras():
    return get_stereo_cameras(config.focal_length,(config.pixelwidthy,config.pixelwidthx),config.baseline,config.camera_pitch)

class StereoTrack():
    def __init__(self):
        self.disparity_offset = config.track_offx
        self.wx,self.wy = track_params[:2] 
        self.sx,self.sy = track_params[2:4]
        self.stereo_wx,self.stereo_wy = stereo_corr_params['ws']
        self.stereo_sxl = stereo_corr_params['sxl'] 
        self.stereo_sxr = stereo_corr_params['sxr'] 
        self.debug=False
        self.proj_cams=generate_stereo_cameras()
        self.reset()

    def reset(self):
        self.ofx,self.ofy=0,0
        self.corr_ref_pat = None
        self.corr_scale_map = None
        self.new_ref=True

    def __corr_scale(selfi,corr): #prioritizing center
        if self.corr_scale_map is None or not corr.shape == self.corr_scale_map:
            self.corr_scale_map=np.zeros(corr.shape)
            crx=corr.shape[0]
            diag=np.array([[i/crx if i<crx/2 else (crx-i)/crx for i in range(crx)]]) +0.5
            diag=diag*0.2+0.8
            corr_scale_map[:,:]=diag
            corr_scale_map[:,:]*=diag.T
            print('doing scale map')
        return corr*self.corr_scale_map #prioritizing center
 
    def __init_left_corr(self,imgl):
        shape=imgl.shape
        wx,wy = self.wx,self.wy
        sx,sy = self.sx,self.sy
        #search window on the left image
        self.cx = cx  = shape[1]//2+self.disparity_offset
        self.cy = cy  = shape[0]//2
        l1,r1=cx-wx//2,cx+wx//2
        u1,d1=cy-wy//2,cy+wy//2
        patern=imgl[u1:d1,l1:r1]
        self.corr_ref_pat=patern.copy()
        self.ofx=self.ofy=0
        self.new_ref=True #sending new reference flag
    


    def __track_left_im(self,imgl):
        wx,wy = self.wx,self.wy
        sx,sy = self.sx,self.sy
        if self.corr_ref_pat is None:
            self.__init_left_corr(imgl)
            return 0,0
        
        cx,cy = self.cx,self.cy

        #search window on current left image
        l2,r2=cx-wx//2-sx+self.ofx,cx+wx//2+sx+self.ofx
        u2,d2=cy-wy//2-sy+self.ofy,cy+wy//2+sy+self.ofy
        search=imgl[u2:d2,l2:r2]
        #corr_search=preprep_corr(search)
        corr_search=search.copy()
        corr = cv2.matchTemplate(corr_search,self.corr_ref_pat,cv2.TM_CCOEFF_NORMED) 
        corr2=self.__corr_scale(corr)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr2)
        x,y = max_loc
        if 1<=x<corr.shape[1]-1 and 1<=y<corr.shape[0]-1:
            dx,dy=polyfit.fit(corr[y-1:y+2,x-1:x+2])
            x+=dx
            y+=dy
            
        ox,oy = x-sx,y-sy
        
        rx=ox+self.ofx
        ry=oy+self.ofy
        self.ofx+=int(ox)
        self.ofy+=int(oy)
        if abs(ox)>sx/3 or abs(oy)>sy/3 or abs(rx)>tx or abs(ry)>ty : #new reference if translate to much
            self.__init_left_corr(imgl)
            return 0,0
        self.new_ref=False
        return rx,ry


    def __track_stereo(self,imgl,imgr): 
        cx,cy=self.cx,self.cy
        wx,wy = self.stereo_wx,self.stereo_wy
        sxl,sxr = self.stereo_sxl, self.stereo_sxr
        cx_off=cx+self.ofx
        cy_off=cy+self.ofy
        l1,r1=cx_off-wx//2,cx_off+wx//2
        u1,d1=cy_off-wy//2,cy_off+wy//2
        patern=imgl[u1:d1,l1:r1]
        corr_pat=patern.copy()
        

        l2,r2=cx_off-wx//2-sxl,cx_off+wx//2+sxr
        #search up and down incase of inacurate camera model
        sy=12
        u2,d2=cy_off-wy//2-sy,cy_off+wy//2+sy
        search=imgr[u2:d2,l2:r2]
        corr_search=search.copy()
        corr = cv2.matchTemplate(corr_search,corr_pat,cv2.TM_CCOEFF_NORMED)    
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr)
        x,y = max_loc
        
        if 1<=x<corr.shape[1]-1 and 1<=y<corr.shape[0]-1:
            dx,dy=polyfit.fit(corr[y-1:y+2,x-1:x+2])
            x+=dx
            y+=dy

        nx=x+(l2-l1)
        ny=y

        offx = x
        offy = y
        
        if self.debug:
            plt.figure('search')
            plt.subplot(2,2,1)
            plt.title('corr_ref_pat')
            plt.imshow(self.corr_ref_pat,cmap='gray')
            plt.subplot(2,2,2)
            plt.title('stereo_pat')
            plt.imshow(patern,cmap='gray')
            plt.subplot(2,2,3)
            plt.title('stereo_search')
            plt.imshow(search,cmap='gray')
            plt.subplot(2,2,4)
            l=len(corr[0,:])
            plt.plot(np.linspace(0,l,l),corr[0,:])
            c2=scipy.signal.resample(corr[0,:],l*4)
            plt.plot(np.linspace(0,l,len(c2)),c2)
            plt.figure('img1/2')
            ax1=plt.subplot(1,2,1)
            plt.imshow(imgl,cmap='gray')
            plt.plot([l1,r1,r1,l1,l1],[u1,u1,d1,d1,u1],'r')
            plt.subplot(1,2,2,sharex=ax1,sharey=ax1)
            plt.imshow(imgr,cmap='gray')
            plt.plot([l2,r2,r2,l2,l2],[u2,u2,d2,d2,u2],'b')
            xx=np.array([l2,l2+wx,l2+wx,l2,l2])+offx
            yy=np.array([u2,u2,u2+wy,u2+wy,u2])+offy
            plt.plot(xx,yy,'r')
            plt.show()
            #import ipdb;ipdb.set_trace()
            self.debug=False
        #print('--->',x,nx,zx)
        return nx,ny

    def __call__(self,imgl,imgr):
        imgl1r=imgl[:,:,0].copy()
        imgr1r=imgr[:,:,0].copy()
        imgl1b=imgl[:,:,2].copy()
        imgr1b=imgr[:,:,2].copy()

        pt_l_x,pt_l_r=self.__track_left_im(imgl1b) #tracked point on left image
        pt_r_x,pt_r_y=self.__track_stereo(imgl1r,imgr1r) #tracked point on right image
            
        range_filt=None
        
        dx,dy=0,0

        res={}

        t_pt = triangulate(self.proj_cams[0],self.proj_cams[1],pt_l_x,pt_l_r,pt_r_x,pt_r_y) 
        res['range']=t_pt[2] # the z position
        
        if self.new_ref:
            self.t_pt = t_pt #save reference point
            self.dx_filt = ab_filt((0,0)) 
            self.dy_filt = ab_filt((0,0)) 
            self.range_filt = ab_filt((res['range'],0))

              
            
        range_f , d_range_f = self.range_filt(res['range'])
            
        if abs(range_f-res['range']) < 0.20:  #range jumps less then 2m per sec (0.2/0.1)
            res['range_f'], res['d_range_f'] = range_f , d_range_f 
            dx = t_pt[0]-self.t_pt[0]
            dy = t_pt[1]-self.t_pt[1]
            if not self.new_ref:
                res['dx']=dx
                res['dy']=dy
                res['dx_f']=self.dx_filt(dx)
                res['dy_f']=self.dy_filt(dy)
            else:
                print('new ref flag')
        else:
            print('new range filt')
            self.range_filt = ab_filt((res['range'],0))

        return res


def draw_track_rects(ret,imgl,imgr):
    wx,wy=config.stereo_corr_params['ws']
    stereo_offx=config.stereo_corr_params['ofx'] #correct search position onright image
    cx = imgl.shape[1]//2
    cx_off_t = cx+config.track_offx
    cy = imgl.shape[0]//2
    draw_rectsr=[] 
    draw_rectsl=[((cx+stereo_offx-wx//2,cy-wy//2) , (cx+stereo_offx+wx//2,cy+wy//2) , (0,0,255))]
    ox=int(ret['disp'])                    
    draw_rectsr.append(((cx+stereo_offx-wx//2+ox,cy-wy//2) , (cx+stereo_offx+wx//2+ox,cy+wy//2) , (0,0,255)))
    ox,oy=int(ret['offx']),int(ret['offy'])
    twx,twy = config.track_params[:2]
    draw_rectsl.append(((cx_off_t-twx//2+1,cy-twy//2+1) , (cx_off_t+twx//2-1,cy+twy//2-1) , (255,255,0)))
    draw_rectsl.append(((cx_off_t-twx//2+ox,cy-twy//2+oy) , (cx_off_t+twx//2+ox,cy+twy//2+oy) , (255,0,255)))
    for rectp in draw_rectsl:
        cv2.rectangle(imgl,*rectp)
    for rectp in draw_rectsr:
        cv2.rectangle(imgr,*rectp)




