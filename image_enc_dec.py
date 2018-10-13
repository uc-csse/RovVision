# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import cv2,sys,struct

bs=(2,2)
lt=[1, 88, 132, 233, 162, 39, 185, 237, 238, 159, 164, 76, 59, 144, 97, 94, 214, 196, 213, 221, 65, 116, 49, 222, 224, 63, 51, 118, 157, 106, 53, 45, 191, 58, 253, 71, 148, 254, 131, 40, 43, 57, 13, 128, 178, 30, 46, 226, 183, 67, 243, 44, 6, 192, 172, 29, 32, 210, 82, 170, 142, 19, 231, 127, 161, 146, 168, 195, 105, 69, 249, 246, 26, 151, 215, 190, 92, 245, 86, 4, 112, 109, 11, 50, 99, 96, 176, 117, 95, 244, 198, 177, 87, 169, 68, 153, 229, 5, 110, 89, 218, 137, 12, 7, 104, 54, 119, 21, 101, 155, 28, 211, 123, 34, 93, 2, 166, 230, 108, 42, 209, 75, 187, 14, 78, 41, 251, 240, 189, 115, 135, 252, 236, 60, 202, 70, 134, 100, 174, 9, 38, 33, 22, 17, 121, 201, 8, 239, 182, 47, 167, 179, 147, 173, 98, 152, 216, 203, 73, 150, 165, 223, 206, 138, 188, 199, 31, 74, 205, 242, 27, 125, 248, 81, 20, 255, 114, 139, 36, 61, 56, 145, 48, 16, 225, 83, 219, 62, 85, 126, 208, 0, 160, 171, 181, 102, 184, 23, 3, 140, 15, 250, 133, 113, 241, 141, 52, 163, 156, 80, 111, 90, 220, 143, 120, 84, 175, 217, 18, 186, 25, 79, 37, 154, 207, 180, 136, 64, 204, 158, 24, 193, 234, 72, 35, 129, 55, 232, 228, 149, 91, 122, 77, 212, 200, 235, 103, 124, 130, 247, 66, 10, 107, 227, 194, 197]
def chksum(num):
    val=sum(struct.unpack('BBBB',struct.pack('I',num%0xffffff)))%256
    return lt[val]

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
    




