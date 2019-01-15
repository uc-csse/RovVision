# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import config
import traceback
import controller
import zmq
import asyncio
import pickle
import time,os,sys
import argparse
import numpy as np
from algs import pid
import utils

parser = argparse.ArgumentParser()
parser.add_argument("--sim",help="run in simulation", action='store_true')
args = parser.parse_args()

topic_postition=config.topic_sitl_position_report

subs_socks=[]
subs_socks.append( utils.subscribe([ config.topic_button,config.topic_axes,config.topic_hat ],config.zmq_pub_joy))
subs_socks.append( utils.subscribe([ config.topic_comp_vis ], config.zmq_pub_comp_vis))
subs_socks.append( utils.subscribe([ config.topic_command ], config.zmq_pub_command))
subs_socks.append( utils.subscribe([ config.topic_imu ], config.zmq_pub_imu))

if args.sim:
    #due to bug in SITL take data directly from fdm_pub_underwater.py in dronesimlab
    sitl_bypass_topic = b'position_rep'
    if 1:
        subs_socks.append( utils.subscribe([ sitl_bypass_topic ],5566) )
        print('************  bypass sitl yaw!')
    bypass_yaw = None


socket_pub = utils.publisher(config.zmq_pub_main)

fb_dir=-1.0
lr_dir=-1.0
ud_dir=-1.0
yaw_dir=-1.0

from config import Joy_map as J

# yaw of -999 used for uninitialised angle
# angles in degrees
mpu_yaw = -999
mpu_yaw_previous = -999
mpu_yaw_velocity = -999

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
lock_range_state=False
lock_yaw_depth_state=False
lock_range=None
lock_yaw_depth=None
track_info = None
joy_axes = [0]*11
ground_range_lock = config.ground_range_lock


async def get_zmq_events():
    global lock_range_state,track_info, lock_range, joy_axes, lock_yaw_depth,lock_yaw_depth_state,ground_range_lock,bypass_yaw
    while True:
        socks=zmq.select(subs_socks,[],[],0)[0]
        for sock in socks:
            ret  = sock.recv_multipart()
            if ret[0]==config.topic_button:
                data=pickle.loads(ret[1])
                print('got button',data)
                if data[config.joy_init_track]==1:
                    #while track_info is None:
                    #    asyncio.sleep(0)
                   if lock_range_state:
                       lock_range_state = False
                   elif not lock_range_state and 'range_f' in track_info:
                        lock_range_state = True
                        if config.lock_mode=='ud_to_range':
                            lock_range = track_info['range_z_f']
                        else:
                            lock_range = track_info['range_f']
                        print('lock range is',lock_range)
                if data[config.joy_depth_hold]==1:
                    lock_yaw_depth_state = not lock_yaw_depth_state
                    #else:
                    #    lock_range = track_info['range']
                controller.update_joy_buttons(data)
            if ret[0]==config.topic_hat:
                print('got hat')
                data=pickle.loads(ret[1])
                controller.update_joy_hat(data)

            if ret[0]==config.topic_axes:
                joy_axes=pickle.loads(ret[1])
                #print('joy',joy_axes)

            if ret[0]==config.topic_comp_vis:
                track_info=pickle.loads(ret[1])

            if ret[0]==config.topic_imu:
                if mpu_yaw_previous == -999:
                    mpu_yaw_previous = np.degrees(pickle.loads(ret[1])['ypr'][0])
                else:
                    mpu_yaw_previous = mpu_yaw
                mpu_yaw = np.degrees(pickle.loads(ret[1])['ypr'][0])
                mpu_yaw_velocity = PID.getDiffAng(mpu_yaw, mpu_yaw_previous) / config.fps

            if ret[0]==config.topic_command:
                try:
                    exec(ret[1])
                except:
                    print('run command_fail')
                    traceback.print_exc(file=sys.stdout)

            if args.sim and ret[0]==sitl_bypass_topic:
                data=pickle.loads(ret[1])
                bypass_yaw = data['yaw']
                #print('-------------topic',track_info)
        await asyncio.sleep(0.001)

start = time.time()
async def control():
    global lock_range_state,track_info,joy_axes,lock_yaw_depth,ud_pid,lr_pid,fb_pid,yaw_pid,ground_range_lock

    ud_pid=pid.PID(*config.ud_params,**config.ud_params_k)
    lr_pid=pid.PID(*config.lr_params)
    fb_pid=pid.PID(*config.fb_params)
    yaw_pid=pid.PID(*config.yaw_params,**config.yaw_params_k)

    ud_cmd,lr_cmd,fb_cmd = 0,0,0
    yaw_cmd=0

    #lr_filt = utils.avg_win_filt(config.lr_filt_size)
    telem={}
    telem['lr_pid']=(0,0,0)
    telem['fb_pid']=(0,0,0)
    telem['ud_pid']=(0,0,0)
    telem['yaw_pid']=(0,0,0)
    cnt=0
    fnum=-1

    while 1:
        if lock_yaw_depth_state and 'yaw' in telem and 'depth' in telem:
            if lock_yaw_depth is None:
                lock_yaw_depth=((np.degrees(telem['yaw'])+360)%360,max((config.minimal_depth_lock,telem['depth'])))
                ud_pid.reset()
                print('lock yaw is {:.2f} depth {:.2f}'.format(*lock_yaw_depth))

            joy_yaw = 0 if abs(joy_axes[J.yaw])<0.008 else joy_axes[J.yaw]

            ud_update = joy_axes[J.ud]/1000.0*config.ud_update_scale

            ground_range=-1
            if track_info is not None and 'range_z' in track_info and config.camera_pitch>np.radians(25):
                ground_range=-track_info['range_z']

            #print('---',abs(joy_axes[J.ud]),ground_range,ground_range_lock)
            if abs(joy_axes[J.ud])<0.1 and ground_range>-1 and ground_range_lock > 0:
                range_delta=ground_range_lock-ground_range
                depth_delta=lock_yaw_depth[1]-telem['depth']

                #print(range_delta,depth_delta)
                #if range_delta>0 and depth_delta>

                if range_delta>0 and depth_delta>-0.1:
                    ud_update-=0.01 # 1cm update less depth

                if range_delta<0 and depth_delta<0.1:
                    ud_update+=0.01


            joy_deltas = (joy_yaw*config.yaw_update_scale, ud_update)
            lock_yaw_depth=((lock_yaw_depth[0]+joy_deltas[0]+360)%360,lock_yaw_depth[1]+joy_deltas[1])

            #yaw_cmd = yaw_dir*yaw_pid(np.degrees(telem['yaw']),lock_yaw_depth[0], -np.degrees(telem['yawspeed'])/config.fps,-joy_yaw)
            yaw_cmd = yaw_dir*yaw_pid(mpu_yaw, lock_yaw_depth[0], mpu_yaw_velocity, -joy_yaw)
            telem['yaw_pid']=(yaw_pid.p,yaw_pid.i,yaw_pid.d)

            if not config.lock_mode=='ud_to_range': #ignoring depth
                ud_cmd = ud_dir*ud_pid(telem['depth'],lock_yaw_depth[1],-telem['climb']/config.fps, joy_axes[J.ud])
                telem['ud_pid']=(ud_pid.p,ud_pid.i,ud_pid.d)

            #else:
            #    ud_cmd = -joy_axes[J.ud]

            telem['lock_yaw_depth']=(*lock_yaw_depth,ground_range,-ground_range_lock)
        else:
            telem['lock_yaw_depth']=(0,0,0,0)
            lock_yaw_depth = None
            yaw_cmd=0
            ud_cmd=0

        if track_info is not None and track_info['fnum']>fnum: #new frame to proccess
            fnum=track_info['fnum']
            #print('---',fnum,track_info['range_f'],lock_range_state)
            if lock_range_state:

                if 'dy' in track_info and not config.lock_mode=='ud_to_range':
                    d_f=track_info['dy_f']
                    lr_cmd = lr_dir*lr_pid(d_f[0],0,d_f[1])
                else:
                    lr_cmd = lr_dir*lr_pid(0,0,0)

                telem['lr_pid']=(lr_pid.p,lr_pid.i,lr_pid.d)

                if config.lock_mode=='fb_to_x':
                    if 'dx' in track_info:
                        d_f=track_info['dx_f']
                        fb_cmd = fb_dir*fb_pid(d_f[0],0,d_f[1])
                    else:
                        fb_cmd = fb_dir*fb_pid(0,0,0)

                if config.lock_mode=='ud_to_range':
                    if 'range_z_f' in track_info: #range is relaible
                        ud_cmd = ud_dir*ud_pid(track_info['range_z_f'],lock_range, track_info['d_range_z_f'])
                    else:
                        ud_cmd = ud_dir*ud_pid(0,0,0) #will send only I information (steady state info)
                telem['ud_pid']=(ud_pid.p,ud_pid.i,ud_pid.d)


                if config.lock_mode=='fb_to_range':
                    if 'range_f' in track_info: #range is relaible
                        fb_cmd = fb_dir*fb_pid(track_info['range_f'],lock_range, track_info['d_range_f'])
                        #print('C {:>5.3f} P {:>5.3f} I {:>5.3f} D {:>5.3f}'.format(fb_cmd,fb_pid.p,fb_pid.i,fb_pid.d))
                    else:
                        fb_cmd = fb_dir*fb_pid(0,0,0) #will send only I information (steady state info)

                telem['fb_pid']=(fb_pid.p,fb_pid.i,fb_pid.d)

                telem['lock_range']=lock_range
#                else:
#                    lock_range_state=False
#                    print('lost lock')

                #if not args.sim:
                #    ud_cmd=0
            else:
                fb_pid.reset()
                lr_pid.reset()
                #ud_cmd = -joy_axes[J.ud]
                #ud_pid.reset()
                #lr_filt.reset()
        if 0: #now only for testing purposes
            if is_joy_override(joy_axes):
                if joy_axes is None:
                    #print('Error joy_axes None',time.time())
                    ud_cmd,fb_cmd,lr_cmd=0,0,0
                else:
                    #print('joy override',time.time())
                    ud_cmd,fb_cmd,lr_cmd,yaw_cmd=\
                            -joy_axes[J.ud],-joy_axes[J.fb],joy_axes[J.lr],joy_axes[J.yaw]


        if (not lock_range_state and joy_axes is not None) or is_joy_override(joy_axes):
            fb_cmd,lr_cmd = -joy_axes[J.fb],joy_axes[J.lr]

        if not lock_yaw_depth and joy_axes is not None:
            ud_cmd,yaw_cmd = -joy_axes[J.ud], joy_axes[J.yaw]


        controller.set_rcs(ud_cmd+config.ud_trim,yaw_cmd,fb_cmd,lr_cmd)

        to_pwm=controller.to_pwm

        telem.update(controller.nav_data)
        if args.sim and bypass_yaw is not None:
            telem['yaw']=np.radians(bypass_yaw%360)
            telem['heading']=bypass_yaw%360


        telem.update({
            'ud_cmd':to_pwm(ud_cmd+config.ud_trim),
            'yaw_cmd':to_pwm(yaw_cmd),
            'lr_cmd':to_pwm(lr_cmd*controller.js_gain),
            'fb_cmd':to_pwm(fb_cmd*controller.js_gain),
            'fnum':fnum,
            'js_gain':controller.js_gain})

        if cnt%100==0: #every 10 sec
            telem['temp']=get_temp()
        telem.update({'ts':time.time()-start, 'lock':lock_range_state, 'joy_axes':joy_axes})
        if fnum>-1:
            socket_pub.send_multipart([config.topic_main_telem,pickle.dumps(telem,-1)])
        cnt+=1
        await asyncio.sleep(0.05)#~20hz control

def is_joy_override(joy_axes):
    if joy_axes is None:
        return False
    tr=0.1
    return abs(joy_axes[J.ud])>tr or abs(joy_axes[J.fb])>tr or abs(joy_axes[J.lr])>tr or abs(joy_axes[J.yaw])>tr


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
