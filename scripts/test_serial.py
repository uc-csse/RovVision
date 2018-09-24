# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import serial
import time
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-b','--baudrate', help="set baudrate", type=int, default=115200)
parser.add_argument('-d','--device', help="set device e.g /dev/ttyUSB0")
parser.add_argument('-t','--type', help="s for sender r for reciver")
parser.add_argument('--rtscts', help="rtscts", action='store_true')
parser.add_argument('--dsrdtr', help="dsrdtr", action='store_true')
parser.add_argument('-bs','--blocksize', help="set the block size", type=int, default=1024)
parser.add_argument('-s','--delay_cycle', help="delay cycle send_time/idle_time in msec default=1000/10 ", default='1000/10')
parser.add_argument('-p','--byte_pattern', help='byte patern to send default a5',default='a5')
args = parser.parse_args()
#pattern=bytes([int(args.byte_pattern,16)]) 
#ser = serial.Serial(args.device,args.baudrate,parity='E',stopbits=2)
pattern=b''
for i in range(0,len(args.byte_pattern),2):
    pattern+=bytes([int(args.byte_pattern[i:i+2],16)]) 

ser = serial.Serial(args.device,args.baudrate, rtscts=args.rtscts, dsrdtr=args.dsrdtr ,stopbits=1)
print(ser,args.blocksize,args.baudrate)
msg_cnt=0
tic=time.time()
send_start=tic
if args.type == 's':
    #to_send = pattern*args.blocksize
    #send_time , idle_time = map(float,args.delay_cycle.split('/'))
    #print('send time = ',send_time, 'idle time = ',idle_time)
    to_send = pattern*(args.blocksize//len(pattern))
    msg_fmt='Sending {:10.3f} Mb/s'
else:
    msg_fmt='Reciving {:10.3f} Mb/s Error Rate {:8.4f}%'
    err_cnt=0    


while 1:
    if args.type == 's':
        td = time.time()-send_start
        if 0 and td>send_time/1000.0:
            if idle_time>0:
                time.sleep(idle_time/1000.0)
                send_start=time.time()
        
        ser.write(to_send)
        if time.time()-tic>1.0:
            #import pdb;pdb.set_trace()
            print(msg_fmt.format(msg_cnt*args.blocksize/(time.time()-tic)/1.e6*8))
            tic=time.time()
            msg_cnt=0
            
    #    tic=time.time()
    else:
        data=ser.read(args.blocksize)
        if len(data):
            err_cnt+=len(data)//len(pattern)-data.count(pattern)
        if time.time()-tic>1.0 and msg_cnt:
            print(msg_fmt.format(msg_cnt*args.blocksize/(time.time()-tic)/1.e6*8,err_cnt/(msg_cnt*args.blocksize)*100))
            print('got',data[0])
            tic=time.time()
            msg_cnt=0
            err_cnt=0
    msg_cnt+=1


