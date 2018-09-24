# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import cv2

def draw_txt(img,vd,md):
    font = cv2.FONT_HERSHEY_SIMPLEX
    #print('-2-',md)
    if 'ts' in md and 'range' in vd and 'temp' in md:
        rng = vd.get('range_avg',vd['range']) 
        line1='{:4.1f}s R{:3.2f}m {:3.1f}C'.format(md['ts'],rng,md['temp'])
        cv2.putText(img,line1,(10,50), font, 0.5,(0,0,255),1,cv2.LINE_AA)

    if 'lock' in md and md['lock']: 
        line2='{:>4}bf {:4.2f}LR'.format(md['fb_cmd'],md['lock_range'])
        if 'ud_cmd' in md:
            line2+=' {:>4}ud {:>4}lr'.format(md['ud_cmd'],md['lr_cmd'])
        cv2.putText(img,line2,(10,100), font, 0.5,(0,0,255),1,cv2.LINE_AA)
    if vd.get('record_state',False):
        cv2.putText(img,'REC '+vd['disk_usage'],(10,200),font, 0.5,(0,0,255),1,cv2.LINE_AA)
    #cv2.putText(img,data_lines['last_cmd_str'][1],(10,250), font, 0.4,(0,0,255),1,cv2.LINE_AA)


