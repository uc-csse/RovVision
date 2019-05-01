# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import cv2
import time
import config

last_valid_range=[0,0]
fps_time=time.time()
frame_start_time=None
frame_start_number=None
fps_last_num=0
fps=None
def draw_txt(img,vd,md):
    global last_valid_range,fps_time,fps,fps_last_num,frame_start_time,frame_start_number
    font = cv2.FONT_HERSHEY_SIMPLEX
    #print('-2-',md)
    if 'ts' in md and 'range' in vd and 'temp' in md:
        line1='{:4.1f}s'.format(md['ts'])
        cv2.putText(img,line1,(10,50), font, 0.5,(0,0,255),1,cv2.LINE_AA)

        rng = vd.get('range_f',vd['range'])
        if rng >20 or rng<0:
            if md['ts']-last_valid_range[0]>1.0: #more than a second not getting valid range
                rng=-1
            else:
                rng = last_valid_range[1]
            color=(0,0,255)
        else:
            last_valid_range = [md['ts'],rng]
            color=(255,255,0)

        line1='R{:3.2f}m'.format(rng)
        cv2.putText(img,line1,(110,50), font, 0.5,color,1,cv2.LINE_AA)


        line1='{:3.1f}C'.format(md['temp'])
        cv2.putText(img,line1,(210,50), font, 0.5,
            (0,0,255) if md['temp']>80 else (0,255,0),1,cv2.LINE_AA)

    if 'lock' in md and md['lock'] and 'lock_range' in md:
        line2='{:>4}bf {:4.2f}LR'.format(md['fb_cmd'],md['lock_range'])
        if 'ud_cmd' in md:
            line2+=' {:>4}ud {:>4}lr'.format(md['ud_cmd'],md['lr_cmd'])
        cv2.putText(img,line2,(10,100), font, 0.5,(0,0,255),1,cv2.LINE_AA)

    if  md.get('lock_yaw_depth',None) is not None:
        if 'ud_cmd' in md and 'yaw_cmd' in md:
            line2=' {:>4}ud {:>4}yaw '.format(md['ud_cmd'],md['yaw_cmd'])
            line2+=' {:03.1f}YL {:03.2f}DL '.format(*md['lock_yaw_depth'])
            cv2.putText(img,line2,(10,130), font, 0.5,(0,0,255),1,cv2.LINE_AA)


    if vd.get('record_state',False):
        cv2.putText(img,'REC '+vd['disk_usage'],(10,200),font, 0.5,(0,0,255),1,cv2.LINE_AA)
    if 'fnum' in vd:
        if frame_start_time is None:
            frame_start_time=time.time()
            frame_start_number=vd['fnum']
        line=' {:>8}'.format(vd['fnum'])
        if vd['fnum']%100==0 and vd['fnum']!=fps_last_num:
            fps=100.0/(time.time()-fps_time)
            #print('---',time.time()-fps_time)
            fps_time=time.time()
            fps_last_num=vd['fnum']
        if fps is not None:
            line+=' {:>.2f}fps'.format(fps)
            line+=' {:>05.2f}delay'.format(\
                (vd['fnum']-frame_start_number)-\
                config.fps*(time.time()-frame_start_time))
        cv2.putText(img,line,(10,500), font, 0.5,(0,0,255),1,cv2.LINE_AA)
    if 'heading' in md:
        y=md['vnav']['ypr'][0] if 'vnav' in md else md['heading']%360
        line='H {:05.1f} D {:06.2f}'.format(y,md['depth'])
        cv2.putText(img,line,(10,480), font, 0.5,(0,0,255),1,cv2.LINE_AA)
        draw_compass(img,750,450,y)
        draw_depth(img,650,20,md['depth'])
    if 'vnav' in md:
        print('vnav',md['vnav'])

from math import cos,sin,pi
def draw_compass(img,x,y,heading):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img,str(int(heading%360)),(x,y), font, 0.5,(0,200,255),1,cv2.LINE_AA)

    r=50.0
    t=(heading-90)/180.0*pi
    cs=cos(t)
    si=sin(t)
    mt=r-3
    cv2.line(img,
        (int(x+cs*(r-mt)),int(y+si*(r-mt))),
        (int(x+cs*r),int(y+si*r)),(0,255,255),1)


    cv2.circle(img, (x,y), int(r), (0,0,255), 1)
    for i in range(36):
        t=i*10/180.0*pi
        if i%9==0:
            mt=10
        elif i%3==0:
            mt=5
        else:
            mt=2
        cs=cos(t)
        si=sin(t)
        cv2.line(img,
                (int(x+cs*(r-mt)),int(y+si*(r-mt))),
                (int(x+cs*r),int(y+si*r)),(0,0,255),1)


def draw_depth(img,x,y,depth):
    l=450
    s=15
    cv2.line(img,(x,y),(x,y+l),(0,0,255))
    for i in range(0,l+1,s):
        if (i//s)%5==0:
            mt=10
        else:
            mt=3
        cv2.line(img,(x,y+i),(x+mt,y+i),(0,0,255))

    d=int(depth*s)
    cv2.line(img,(x,y+d),(x+10,y+d),(0,255,255))
    cv2.line(img,(x,y+d+1),(x+10,y+d+1),(255,0,255))
