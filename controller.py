# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from pymavlink import mavutil

#pymavlink documentation for bluerov2
#https://www.ardusub.com/developers/pymavlink.html


import numpy as np
import zmq
import sys,os
import time
import pickle
#import config
import asyncio
import config

mav1 = None
event = None
__pos = None

#chan 3 up/down (right fwd/bck)
#chan 4 yaw (right right/left)
#chan 5 fwd/back  (left fwd,back)
#chan 6 lef/right (left left,right)

#joy axes mapping
class R:
    ud=2
    yaw=3
    fb=4
    lr=5
    lights1=8



def get_pos():
    return __pos

def to_pwm(val):
    return int(val*300)+1500

def ___set_rcs(ud, yaw, fb, lr):
    global mav1
    values = [ 1500 ] * 9
    #values[8]=1100
    values[R.ud] = to_pwm(ud)
    values[R.yaw] = to_pwm(yaw)
    values[R.fb] = to_pwm(fb)
    values[R.lr] = to_pwm(lr)
    values[R.lights1] = lights1
    #print(values) 
    mav1.mav.rc_channels_override_send(mav1.target_system, mav1.target_component, *values)

def set_rcs(ud, yaw, fb, lr):
    global lights1
    buttons=0
    if lights1!=0:
        if lights1>0:
            buttons+=(1<<14)
        else:
            buttons+=(1<<13)
        lights1=0
    #revers engineer the code in:
    #https://github.com/bluerobotics/ardusub/blob/master/ArduSub/joystick.cpp
    #function Sub::transform_manual_control_to_rc_override
    # had to use mav1.mav.manual_control_send to be able to control the lights 

    #throttleScale = 0.8*gain*g.throttle_gain
    throttleBase = 500#/throttleScale
    tr=ud*tr_gain*1000+throttleBase
    #print(tr)
    mav1.mav.manual_control_send(mav1.target_system,
            int(fb*js_gain*1000),int(lr*js_gain*1000),int(tr),int(yaw*1000),buttons)


#lights1=1100
def ___update_joy_hat(hat):
    global lights1
    lights1+=hat[1]*100
    lights1=max(1100,min(2000,lights1))
    print('got hat',hat,lights1) 

lights1=0
js_gain=1.0
tr_gain=0.5
def update_joy_hat(hat):
    global lights1,js_gain
    lights1=hat[0]
    #lights1=max(1100,min(2000,lights1))
    #print('got hat',hat,lights1) 
    js_gain+=hat[1]*0.05
    js_gain=min(max(js_gain,0.1),2.0)
    print('*'*10+'GAIN {:.1f}'.format(js_gain))

def update_joy_buttons(data):
    if data[config.joy_arm]==1:
        mav1.mav.command_long_send(
                mav1.target_system,
                mav1.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0, 1, 0, 0, 0, 0, 0, 0)

    if data[config.joy_disarm]==1:
        mav1.mav.command_long_send(
            mav1.target_system,
            mav1.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 0, 0, 0, 0, 0, 0, 0)

    if data[config.joy_depth_hold]==1:
        mode_id = mav1.mode_mapping()['ALT_HOLD']
        mav1.mav.set_mode_send(
            mav1.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id)

    if data[config.joy_manual]==1:
        mode_id = mav1.mode_mapping()['MANUAL'] #maybe STABILIZE
        mav1.mav.set_mode_send(
            mav1.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id)


joy_axes=None
def update_joy_axes(data):
    global joy_axes
    joy_axes=np.array(data)


def get_rcs():
    global mav1
    if 'RC_CHANNELS_RAW' in mav1.messages:
        return [mav1.messages['RC_CHANNELS_RAW'].to_dict()['chan%d_raw'%(i+1)] for i in range(8)]


def get_position_struct(mav):
    d={}
    if 'VFR_HUD' in mav1.messages:
        #import pdb;pdb.set_trace()
        d['posz']=mav1.messages['VFR_HUD'].alt
    if 'SIMSTATE' in mav1.messages:
        sm=mav1.messages['SIMSTATE']
        d['yaw']=np.degrees(sm.yaw)
        d['roll']=np.degrees(sm.roll)
        d['pitch']=np.degrees(sm.pitch)
    if {'SIMSTATE','HOME'} in set(mav1.messages):
        #import pdb;pdb.set_trace()
        home=mav1.messages['HOME']
        lng_factor=np.cos(np.radians(sm.lng/1.0e7))
        earth_rad_m=6371000.0
        deg_len_m=earth_rad_m*np.pi/180.0
        d['posx']=(sm.lng-home.lon)/1.0e7*lng_factor*deg_len_m
        d['posy']=(sm.lat-home.lat)/1.0e7*deg_len_m
    return d

def init():
    global mav1,event
    #mav1 = mavutil.mavlink_connection('udp:127.0.0.1:14551')
    #mav1 = mavutil.mavlink_connection('udp:192.168.3.1:14551')
    mav1 = mavutil.mavlink_connection('udp:0.0.0.0:14551')
    #mav1 = mavutil.mavlink_connection(os.environ['ST_RASP_MAV'])
    if __name__=='__main__':
        event = mavutil.periodic_event(0.3)
    freq=30
    pub_position_event = mavutil.periodic_event(freq)

    print("Waiting for HEARTBEAT")
    mav1.wait_heartbeat()
    print('Version: WIRE_PROTOCOL_VERSION',str(mav1.mav))
    print("Heartbeat from APM (system %u component %u)" % (mav1.target_system, mav1.target_system))
    #set_rcs(1510,1510,1510,1510)
    #print(mav1.param_fetch_one(b'JS_GAIN_DEFAULT'))

    mav1.mav.param_request_read_send(
       mav1.target_system, mav1.target_component,
           b'JS_GAIN_DEFAULT',
               -1,
               mavutil.mavlink.MAV_PARAM_TYPE_REAL32
               )
    # Print new value in RAM
    message = mav1.recv_match(type='PARAM_VALUE', blocking=True).to_dict()

    js_gain_default=message['param_value']

    
    mav1.mav.param_set_send( mav1.target_system, mav1.target_component,
        b'JS_THR_GAIN',
        1.0,
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )
    message = mav1.recv_match(type='PARAM_VALUE', blocking=True).to_dict()
    js_th_gain=message['param_value']
    print('JS_THR_GAIN={} JS_GAIN_DEFAULT={}'.format(js_th_gain,js_gain_default))

async def run(socket_pub=None):
    global mav1,event,__pos
    while True:
        time.sleep(0)
        ret=mav1.recv_msg()
        if ret is not None:
            if socket_pub is not None:
                socket_pub.send_multipart([config.topic_mav_telem, pickle.dumps(ret.to_dict(),-1)])
            __pos=get_position_struct(mav1)
        
        if __pos  and event is not None and event.trigger():
            print(__pos)
            #print('X:%(posx).1f\tY:%(posy).1f\tZ:%(posz).1f\tYW:%(yaw).0f\tPI:%(pitch).1f\tRL:%(roll).1f'%__pos)
        await asyncio.sleep(0.001) 

async def test_lights():
    global lights1
    await asyncio.sleep(1)
    lights1=1600
    set_rcs(0,0,0,0)
    print('lights on?')
    import inspect
    print(inspect.getfile(mav1.mav.rc_channels_override_send)) 
    await asyncio.sleep(3)
    lights1=1100
    set_rcs(0,0,0,0)
    print('lights off?')



if __name__=='__main__':
    init()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        run(),test_lights()
        ))
    loop.close()
