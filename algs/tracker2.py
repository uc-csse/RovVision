# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import polyfit
import cv2
import scipy
import scipy.signal
import sys

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
        self.ref_cnt=0
        self.reset()

    def reset(self):
        self.ofx,self.ofy=self.disparity_offset,0
        self.corr_ref_pat = None
        self.corr_scale_map = None
        self.new_ref=True
        self.t_pt=None

    def __corr_scale(self,corr): #prioritizing center
        if corr.shape[0] != corr.shape[1]: #skip incase of not semetric (to complicated :)
            return corr
        if self.corr_scale_map is None or not corr.shape == self.corr_scale_map.shape:
            self.corr_scale_map=np.zeros(corr.shape)
            crx=corr.shape[0]
            diag=np.array([[i/crx if i<crx/2 else (crx-i)/crx for i in range(crx)]]) +0.5
            diag=diag*0.2+0.8
            self.corr_scale_map[:,:]=diag
            self.corr_scale_map[:,:]*=diag.T
            print('doing scale map')
        return corr*self.corr_scale_map #prioritizing center

    def __init_left_corr(self,imgl):
        shape=imgl.shape
        wx,wy = self.wx,self.wy
        sx,sy = self.sx,self.sy

        self.ofx= self.disparity_offset
        self.ofy=0
        cx  = shape[1]//2+self.ofx
        cy  = shape[0]//2+self.ofy
        #search window on the left image
        l1,r1=cx-wx//2,cx+wx//2
        u1,d1=cy-wy//2,cy+wy//2

        if 1:
            #replace the center with better one
            good_ftr = cv2.goodFeaturesToTrack(imgl[u1:d1,l1:r1].copy(),1,0.01,10)
            if good_ftr is not None:
                goot_pt = good_ftr[0][0]
                self.ofx += int(goot_pt[0]) - wx//2
                self.ofy += int(goot_pt[1]) - wy//2
                cx  = shape[1]//2+self.ofx
                cy  = shape[0]//2+self.ofy
                l1,r1=cx-wx//2,cx+wx//2
                u1,d1=cy-wy//2,cy+wy//2

        patern=imgl[u1:d1,l1:r1]
        self.corr_ref_pat=patern.copy()
        self.new_ref=True #sending new reference flag
        self.ref_cnt+=1

        #print('init----leftcorr')



    def __track_left_im(self,imgl):
        wx,wy = self.wx,self.wy
        sx,sy = self.sx,self.sy
        cx,cy = imgl.shape[1]//2,imgl.shape[0]//2
        if self.corr_ref_pat is None:
            print('--- init corr patern')
            self.__init_left_corr(imgl)
            return cx+self.ofx,cy


        #search window on current left image
        l2,r2=cx-wx//2-sx+self.ofx,cx+wx//2+sx+self.ofx
        u2,d2=cy-wy//2-sy+self.ofy,cy+wy//2+sy+self.ofy
        search=imgl[u2:d2,l2:r2]

        if l2<0 or u2<0 or r2>imgl.shape[1] or d2>imgl.shape[1]:
            print('track break too close to edge')
            self.__init_left_corr(imgl)
            return cx+self.ofx,cy

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
        if abs(ox)>(sx*2/3) or abs(oy)>(sy*2/3): # or abs(rx)>tx or abs(ry)>ty : #new reference if translate to much
            print('track break too big translate')
            self.__init_left_corr(imgl)
            return cx+self.ofx,cy
        self.new_ref=False
        return rx+cx,ry+cy


    def __track_stereo(self,imgl,imgr):
        cx,cy = imgl.shape[1]//2,imgl.shape[0]//2
        wx,wy = self.stereo_wx,self.stereo_wy
        sxl,sxr = self.stereo_sxl, self.stereo_sxr
        cx_off=cx+self.ofx
        cy_off=cy+self.ofy
        l1,r1=cx_off-wx//2,cx_off+wx//2
        u1,d1=cy_off-wy//2,cy_off+wy//2
        patern=imgl[u1:d1,l1:r1]
        corr_pat=patern.copy()


        l2,r2=cx_off-wx//2-sxl,cx_off+wx//2+sxr
        l2=np.clip(l2,0,imgl.shape[1]-1)
        r2=np.clip(r2,0,imgl.shape[1]-1)

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
        ny=y-sy


        rx,ry =  nx+cx_off,ny+cy_off
        if self.debug:
            import matplotlib
            import matplotlib.pyplot as plt
            plt.figure('search {}'.format(self.debug))
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
            xx=[rx-wx/2,rx+wx/2,rx+wx/2,rx-wx/2,rx-wx/2]
            yy=[ry-wy/2,ry-wy/2,ry+wy/2,ry+wy/2,ry-wy/2]
            plt.plot(xx,yy,'r')
            plt.show()
            #import ipdb;ipdb.set_trace()
            self.debug=False
        #print('--->',x,nx,zx)
        return rx,ry

    def __validate(self, pt_l, pt_r, imgr):
        #checks that the corr pattern is in the middle of the right image point
        wx,wy = self.wx,self.wy
        sx,sy = 30,30

        if abs(pt_l[1]-pt_r[1])>=5: #not supposed to be a diffrence in hight in stereo
            print('track stereo fail ',pt_l[1]-pt_r[1])
            return False


        l,r=int(pt_r[0])-wx//2-sx , int(pt_r[0])+wx//2+sx
        u,d=int(pt_r[1])-wy//2-sy , int(pt_r[1])+wy//2+sy

        if l<0 or u<0 or r>imgr.shape[1] or d>imgr.shape[0]:
            #print('validate reach limits lurd',l,u,r,d)
            return False

        spatern=imgr[u:d,l:r].copy()
        corr = cv2.matchTemplate(spatern,self.corr_ref_pat,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr)
        x,y = max_loc
        x=x - sx
        y=y - sy

        if abs(x) <= 15 and abs(y)<=15:
            return True
        print('valid failed ',x,y)
        return False



    def __track_and_validate(self, imgl1r, imgr1r, imgl1b, imgr1b):

        pt_l_x,pt_l_y=self.__track_left_im(imgl1b) #tracked point on left image
        pt_r_x,pt_r_y=self.__track_stereo(imgl1r,imgr1r) #tracked point on right image

        valid = self.__validate((pt_l_x,pt_l_y),(pt_r_x,pt_r_y),imgr1r)
        return valid,pt_l_x,pt_l_y,pt_r_x,pt_r_y

    def __call__(self,imgl,imgr):
        imgl1r=imgl[:,:,0].copy()
        imgr1r=imgr[:,:,0].copy()
        imgl1b=imgl[:,:,2].copy()
        imgr1b=imgr[:,:,2].copy()
        valid,pt_l_x,pt_l_y,pt_r_x,pt_r_y = self.__track_and_validate(imgl1r, imgr1r, imgl1b, imgr1b )
        if not valid:
            self.__init_left_corr(imgl1b)
            valid,pt_l_x,pt_l_y,pt_r_x,pt_r_y = self.__track_and_validate(imgl1r, imgr1r, imgl1b, imgr1b )
        res={'valid':valid}
        res['pt_l']=(pt_l_x,pt_l_y)
        res['pt_r']=(pt_r_x,pt_r_y)
        res['range']=-100
        if not valid:
            self.__init_left_corr(imgl1b)
            self.t_pt=None
            self.last_t_pt=None
        else:

            t_pt = triangulate(self.proj_cams[0],self.proj_cams[1],pt_l_x,pt_l_y,pt_r_x,pt_r_y)

            res['range']=t_pt[0] # range in the x direction
            res['range_z']=t_pt[2] # range in the z direction


        #if valid:#abs(range_f-res['range']) < 0.20:  #range jumps less then 2m per sec (0.2/0.1)
            #if self.new_ref:
            if self.new_ref or self.t_pt is None:
                self.t_pt = t_pt #save reference point
                self.last_t_pt = None
                #self.dx_filt = ab_filt((0,0))
                self.range_filt = ab_filt((res['range'],0))
                self.range_filt_z = ab_filt((res['range_z'],0))
                self.dx_filt = ab_filt((0,0))
                self.dy_filt = ab_filt((0,0))
                self.dz_filt = ab_filt((0,0))


            range_f , d_range_f = self.range_filt(res['range'])
            range_z_f , d_range_z_f = self.range_filt_z(res['range_z'])
            res['range_f'], res['d_range_f'] = range_f , d_range_f
            res['range_z_f'], res['d_range_z_f'] = range_z_f , d_range_z_f
            dx = (t_pt[0]-self.t_pt[0])
            dy = (t_pt[1]-self.t_pt[1])
            #print('----',dy)
            dz = (t_pt[2]-self.t_pt[2])
            if not self.new_ref:
                res['dx']=dx
                res['dy']=dy
                res['dz']=dz
                res['dx_f']=self.dx_filt(dx)
                res['dy_f']=self.dy_filt(dy)
                res['dz_f']=self.dz_filt(dz)
            else:
                print('new ref flag 1')
        #else:
        #    print('new range filt')
        #    self.range_filt = ab_filt((res['range'],0))
            self.last_t_pt=t_pt

        res['ref_cnt']=self.ref_cnt
        return res


def draw_track_rects(ret,imgl,imgr):
    wx,wy=config.stereo_corr_params['ws']

    if 'disp' in ret: #old format
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
    else:
        wx_t,wy_t = config.track_params[:2]
        wx_s,wy_s = config.stereo_corr_params['ws']
        if 'pt_r' in ret:
            xl,yl=map(int,ret['pt_l'])
            xr,yr=map(int,ret['pt_r'])
            valid = ret.get('valid',False)
            if valid:
                col = (0,255,0)
            else:
                col = (0,0,255)
            cv2.rectangle(imgl,(xl-wx_t//2,yl-wy_t//2),(xl+wx_t//2,yl+wy_t//2),col)
            cv2.rectangle(imgl,(xl-wx_s//2,yl-wy_s//2),(xl+wx_s//2,yl+wy_s//2),col)
            cv2.rectangle(imgr,(xr-wx_s//2,yr-wy_s//2),(xr+wx_s//2,yr+wy_s//2),col)
