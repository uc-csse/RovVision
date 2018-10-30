# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import config
import controller
import zmq
import asyncio
import pickle
import time,os
import argparse
from algs import pid


parser = argparse.ArgumentParser()
parser.add_argument("--sim",help="run in simulation", action='store_true')
args = parser.parse_args()

topic_postition=config.topic_sitl_position_report

context = zmq.Context()
zmq_sub_joy = context.socket(zmq.SUB)
zmq_sub_joy.connect("tcp://127.0.0.1:%d" % config.zmq_pub_joy)
zmq_sub_joy.setsockopt(zmq.SUBSCRIBE,config.topic_button)
zmq_sub_joy.setsockopt(zmq.SUBSCRIBE,config.topic_axes)
zmq_sub_joy.setsockopt(zmq.SUBSCRIBE,config.topic_hat)

zmq_sub_v3d = context.socket(zmq.SUB)
zmq_sub_v3d.connect("tcp://127.0.0.1:%d" % config.zmq_pub_comp_vis)
zmq_sub_v3d.setsockopt(zmq.SUBSCRIBE,config.topic_comp_vis)


socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://127.0.0.1:%d" % config.zmq_pub_main )

fb_dir=-1.0
lr_dir=-1.0


class J:
    ud=4
    yaw=3
    fb=1
    lr=0

#if args.sim:
#    idle_cmd=1500
#else:
#    idle_cmd=0xffff


def get_temp():
    cmd="sensors -u |grep temp1_input |gawk '{ print $2 }'"
    try:
        return float(os.popen(cmd).read())
    except:
        return -100

## system states 
lock_state=False
lock_range=None
track_info = None
joy_axes = None

async def get_zmq_events():
    global lock_state,track_info, lock_range, joy_axes
    while True:
        socks=zmq.select([zmq_sub_joy,zmq_sub_v3d],[],[],0)[0]
        for sock in socks:
            ret  = sock.recv_multipart()
            if ret[0]==config.topic_button:
                data=pickle.loads(ret[1])
                print('git button',data)
                if data[5]==1:
                    #while track_info is None:
                    #    asyncio.sleep(0)
                   if lock_state:
                       lock_state = False
                   elif not lock_state and 'range_avg' in track_info:
                        lock_state = True
                        lock_range = track_info['range_avg']
                        print('lock range is',lock_range)
                    #else:
                    #    lock_range = track_info['range']
                controller.update_joy_buttons(data)
            if ret[0]==config.topic_hat:
                print('git hat')
                data=pickle.loads(ret[1])
                controller.update_joy_hat(data)

            if ret[0]==config.topic_axes:
                joy_axes=pickle.loads(ret[1])
                #print('joy',joy_axes)
               
            if ret[0]==config.topic_comp_vis:
                track_info=pickle.loads(ret[1])
                #print('-------------topic',track_info)
        await asyncio.sleep(0.001) 

start = time.time()
async def control():
    global lock_state,track_info,joy_axes

    ### y
    scl=20
    ud_params=(0.5*scl,0.005*scl,0.5*scl,0.3*scl)
    ud_pid=pid.PID(*ud_params)
    
    ### x
    scl=6
    lr_params=(0.42*scl,0.004*scl,1.6*scl,0.4*scl)
    lr_pid=pid.PID(*lr_params)
    
    ### range
    scl=12
    fb_params=(0.24*scl,0.002*scl,2.2*scl,0.4*scl)
    fb_pid=pid.PID(*fb_params)

    ud_cmd,lr_cmd,fb_cmd = 0,0,0 
    yaw_cmd=0


    telem={}
    cnt=0
    while 1:
        if track_info is not None and lock_state:
            if 'dy' in track_info: 
                ud_cmd = ud_pid(track_info['dy'],0)
                #ud_cmd=int(ud_cmd*2000+1500)
            else:
                ud_pid=pid.PID(*ud_params)
                #ud_cmd=1500
            
            if 'dx' in track_info: 
                lr_cmd = lr_dir*lr_pid(track_info['dx'],0)
                #lr_cmd=int(-lr_cmd*300+1500)
                #print('C {:>5.3f} P {:>5.3f} I {:>5.3f} D {:>5.3f}'.format(lr_cmd,lr_pid.p,lr_pid.i,lr_pid.d))
            else:
                #print('rest lr loop')
                lr_pid=pid.PID(*lr_params)
                #lr_cmd=1500

            range_key = 'range_avg'

            if range_key in track_info: 
                fb_cmd = fb_dir*fb_pid(track_info[range_key],lock_range)
                #print('C {:>5.3f} P {:>5.3f} I {:>5.3f} D {:>5.3f}'.format(fb_cmd,fb_pid.p,fb_pid.i,fb_pid.d))
                #fb_cmd=int(fb_dir*fb_cmd*300+1500)
            else:
                fb_pid=pid.PID(*fb_params)
            #print('-----------',ud_cmd,lr_cmd,fb_cmd,lock_range)
            

            if not args.sim:
                ud_cmd=0
            to_pwm=controller.to_pwm
            telem.update({\
                    'ud_cmd':to_pwm(ud_cmd),'lr_cmd':to_pwm(lr_cmd*controller.js_gain),
                    'fb_cmd':to_pwm(fb_cmd*controller.js_gain),'lock_range':lock_range,'fnum':track_info['fnum']})
            track_info = None
            #controller.set_rcs_diff(ud_cmd,idle_cmd,fb_cmd,lr_cmd,idle_val=idle_cmd)
            #controller.set_rcs(ud_cmd,idle_cmd,fb_cmd,lr_cmd)
        else:
            if joy_axes is None:
                ud_cmd,fb_cmd,lr_cmd=0,0,0
            else:
                scl=1.0
                ud_cmd,fb_cmd,lr_cmd,yaw_cmd=\
                        -joy_axes[J.ud]*scl,-joy_axes[J.fb]*scl,joy_axes[J.lr]*scl,joy_axes[J.yaw]*scl
        controller.set_rcs(ud_cmd,yaw_cmd,fb_cmd,lr_cmd)

        if cnt%100==0: #every 10 sec
            telem['temp']=get_temp()
        telem.update({'ts':time.time()-start, 'lock':lock_state}) 
        socket_pub.send_multipart([config.topic_main_telem,pickle.dumps(telem,-1)]) 
        cnt+=1
        await asyncio.sleep(0.05)#~20hz control 


def init():
    controller.init()

if __name__=='__main__':
    init()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        controller.run(socket_pub),
        get_zmq_events(),
        control(),
        ))
    loop.close()

