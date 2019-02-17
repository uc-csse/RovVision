# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import cv2

last_valid_range=[0,0]
def draw_txt(img,vd,md):
    global last_valid_range
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
        line=' {:>8}'.format(vd['fnum'])
        cv2.putText(img,line,(10,500), font, 0.5,(0,0,255),1,cv2.LINE_AA)
    if 'heading' in md:
        line='H {:05.1f} D {:06.2f}'.format(md['heading']%360,md['depth'])
        cv2.putText(img,line,(10,480), font, 0.5,(0,0,255),1,cv2.LINE_AA)

    #cv2.putText(img,data_lines['last_cmd_str'][1],(10,250), font, 0.4,(0,0,255),1,cv2.LINE_AA)
