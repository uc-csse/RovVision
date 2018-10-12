# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import cv2,sys,struct

bs=(2,2)

def chksum(num):
    return sum(struct.unpack('BBBB',struct.pack('I',num+11*7)))%256

def encode(img,num):
    bits=[0 if i=='0' else 255 for i in '{:032b}'.format(num)]
    bits+=[0 if i=='0' else 255 for i in '{:08b}'.format(chksum(num))]
    start_y=img.shape[0]-bs[0]
    for i,b in enumerate(bits):
        img[start_y:start_y+bs[0],i*bs[0]:(i+1)*bs[1],:]=b

def decode(img):
    ret=0
    chk=0
    start_y=img.shape[0]-bs[0]
    for i in range(32+8):
        av=img[start_y:start_y+bs[0],i*bs[0]:(i+1)*bs[1],:].sum()//(bs[0]*bs[1]*3)
        if av>128:
            if i<32:
                ret+=2**(32-1-i)
            else:
                chk+=2**(8-1-(i-32))
    if chksum(ret)==chk:
        return ret

if 0 and __name__=='__main__':
    img=np.zeros((200,100,3),dtype='uint8')
    encode(img,1760)
    print(decode(img))
    cv2.imshow('jjj',img)
    cv2.waitKey(0)

if 1 and __name__=='__main__':
    from subprocess import Popen,PIPE
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("test")

    img_counter = 0
    cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=150 key-int-max=100 ! filesink location=out.h264"
    gstsrc = 'fdsrc ! videoparse width={} height={} format=15 ! videoconvert ! video/x-raw, format=I420'#.format(sx,sy) #! autovideosink'


    for i in range(100):
        print('--',i)
        ret, frame = cam.read()
        sy,sx,_=frame.shape
        if i==0:
            gcmd=cmd.format(gstsrc.format(sx,sy))
            pp = Popen(gcmd, shell=True, bufsize=0,stdin=PIPE, stdout=sys.stdout, close_fds=False)
            
        encode(frame,i)
        pp.stdin.write(frame.tostring())

        cv2.imshow("test", frame)
        if not ret:
            break
        k = cv2.waitKey(1)

        if k%256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break

    pp.stdin.close()
    del pp

#if 1 and __name__=='__main__':
#    from subprocess import Popen,PIPE
#    sx,sy=640,480
    cmd='gst-launch-1.0 -q filesrc location=out.h264 ! h264parse ! decodebin ! videoconvert ! video/x-raw,height={},width={},format=RGB ! fdsink  sync=false'
    pp=Popen(cmd.format(sy,sx) , shell=True, stdout=PIPE, bufsize=0)
    for i in range(100):
        data=pp.stdout.read(sx*sy*3)
        img=np.fromstring(data,'uint8').reshape([sy,sx,3])
        d=decode(img)
        if i!=d:
            print('error {},{}'.format(i,d))
    




