# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#to run recording include optitrack:

#first find the rigid body number by running optitrack.py in the example below is 3
#python gy86.py --prefix data/manuvers_optitrack/test%s --video 1 --dev 1 --rec --opti_track=3

import serial,time,struct,math
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('../')
from mpl_toolkits.mplot3d import Axes3D
import argparse
import time,zmq
import pickle
import config
import utils


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--send_start",help="sends 02 01 03", action='store_true')
    parser.add_argument("-u","--usbdevice",help="sets usbdevice default /dev/ttyUSB1",default='/dev/ttyUSB1')
    args = parser.parse_args()


socket_pub = utils.publisher(config.zmq_pub_imu)

zmq_sub_joy = utils.subscribe([config.topic_button],config.zmq_pub_joy)

zmq_sub_v3d = utils.subscribe([config.topic_comp_vis_cmd],config.zmq_pub_comp_vis)

lmap = lambda func, *iterable: list(map(func, *iterable))


def reader():
    laser1_status=False

    ser = serial.Serial(args.usbdevice,460800)
    ser.flush()
    while ser.inWaiting():
        ser.read()#flushing

    #start triggering
    if args.send_start:
        print('sending start')
        ser.write(b'\x01')
    #ser.flush()
    print('done flushing..')
    while 1:
        #while ser.inWaiting()<2:
        #    yield None
        if zmq_sub_joy.poll(0):
            ret  = zmq_sub_joy.recv_multipart()
            if ret[0]==config.topic_button:
                data=pickle.loads(ret[1])
                if data[config.joy_toggle_laser1]==1:
                    laser1_status = not laser1_status
                    if laser1_status:
                        ser.write(b'\x03')
                    else:
                        ser.write(b'\x04')

        if 1 and zmq_sub_v3d.poll(0):
            print('got')
            ret  = zmq_sub_v3d.recv_multipart()
            if ret[0] == config.topic_comp_vis_cmd:
                if ret[1] == b'start_trig':
                    print('start trig')
                    ser.write(b'\x01')

        while 1:#ser.inWaiting():
            if ser.read()==b'\xa5':
                if ser.read()==b'\xa5':
                    break
        #synced
        ret={}
        fmt='='+'h'*9+'fiI'
        raw_data=ser.read(struct.calcsize(fmt))
        chksum=struct.unpack('=H',ser.read(2))[0]

        calc_chksum=sum(struct.unpack('H'*(struct.calcsize(fmt)//2),raw_data))%2**16
        #if chksum!=calc_chksum:
        #    print('Error, bad checksum',chksum,calc_chksum)
        #    continue

        data=struct.unpack(fmt,raw_data)
        ret['a/g']=np.array(lmap(float,data[:6]))
        ret['mag']=np.array(lmap(float,data[6:9]))
        ret['therm']=data[9]
        ret['baro']=data[10]
        ret['t_stemp_ms']=data[11]/1000.0
        #print('==== {:.3f}'.format(data[10]/1e6))
        yield ret

def ploter():
    fig = plt.figure(figsize=(8,6))
    ax1 = fig.add_subplot(4, 1, 1)
    ax1.set_title('acc')
    ax2 = fig.add_subplot(4, 1, 2)
    ax2.set_title('gyro')
    ax3 = fig.add_subplot(4, 1, 3)
    ax3.set_title('mag')
    ax4 = fig.add_subplot(4, 1, 4)
    ax4.set_title('alt')
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
        gy_data=yield
        history=history[-mem_len:]
        history.append(gy_data)

        if time.time()-last_plot<0.2 and cnt%10!=0:
            continue
        last_plot=time.time()

        for hdl in hdl_list:
            hdl[0].remove()
        hdl_list=[]

        acc_gyro=np.array(lmap(lambda x:x['a/g'],history))
        mag=np.array(lmap(lambda x:x['mag'],history))
        alt=np.array(lmap(lambda x:x['alt'],history))
        #ts=np.array(lmap(lambda x:x['t_stemp_ms']/1000.0,history))
        if 's_sync' in gy_data:
            ts=np.array(lmap(lambda x:x['s_sync']/1000.0,history))
        else:
            ts=np.array(lmap(lambda x:x['t_stemp_ms']/1000.0,history))
        if alt_ref is None:
            alt_ref=alt[0]

        hdl_list.append(ax1.plot(ts,acc_gyro[:,0],'-b',alpha=0.5))
        hdl_list.append(ax1.plot(ts,acc_gyro[:,1],'-g',alpha=0.5))
        hdl_list.append(ax1.plot(ts,acc_gyro[:,2],'-r',alpha=0.5))
        ax1.set_xlim(ts.min(),ts.max())

        hdl_list.append(ax2.plot(ts,acc_gyro[:,3],'-b',alpha=0.5))
        hdl_list.append(ax2.plot(ts,acc_gyro[:,4],'-g',alpha=0.5))
        hdl_list.append(ax2.plot(ts,acc_gyro[:,5],'-r',alpha=0.5))
        ax2.set_xlim(ts.min(),ts.max())

        hdl_list.append(ax3.plot(ts,mag[:,0],'-b',alpha=0.5))
        hdl_list.append(ax3.plot(ts,mag[:,1],'-g',alpha=0.5))
        hdl_list.append(ax3.plot(ts,mag[:,2],'-r',alpha=0.5))
        ax3.set_xlim(ts.min(),ts.max())

        hdl_list.append(ax4.plot(ts,alt-alt_ref,'-r',alpha=0.5))
        ax4.set_xlim(ts.min(),ts.max())
        #if cnt<100:
        fig.canvas.draw()
        plt.waitforbuttonpress(timeout=0.001)

if  __name__=="__main__":
    rd=reader()
    #rd=file_reader(prefix+'.pkl')
    #plot=ploter()
    #plot.__next__()
    cnt=0
    last_t=0
    while 1:
        data=rd.__next__()
        #print(data)
        if data is not None:
            if 'a/g' in data:
                socket_pub.send_multipart([config.topic_imu,pickle.dumps(data,-1)])
                tdiff = data['t_stemp_ms']-last_t
                last_t = data['t_stemp_ms']
                if cnt%50==0:
                    fmt='{:7.2f} '*6 + '{:2.4f}'
                    print(fmt.format(*(data['a/g'][:3]),*data['mag'],tdiff))
                #plot.send(data)
                cnt+=1
        else:
            #print('Error data is None')
            time.sleep(0.001)
            #if (k%256)==27:
            #    break
