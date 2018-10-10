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



def get_pos():
    return __pos

def to_pwm(val):
    return int(val*200)+1500

def set_rcs(ud, yaw, fb, lr):
    global mav1
    values = [ 1500 ] * 8
    values[R.ud] = to_pwm(ud)
    values[R.yaw] = to_pwm(yaw)
    values[R.fb] = to_pwm(fb)
    values[R.lr] = to_pwm(lr)
    #print(values) 
    mav1.mav.rc_channels_override_send(mav1.target_system, mav1.target_component, *values)

def set_rcs_diff(ud, yaw, fb, lr, idle_val):
    out_values = [ idle_val for i in range(8)] 
    in_values=get_rcs()

    if in_values is None:
        print('Warning no in_values from rcs')
        in_values=out_values.copy()
    if yaw != idle_val:
        out_values[3]=in_values[3]+(yaw-1500)
    if fb != idle_val:
        out_values[4]=in_values[4]+(fb-1500) 
    if lr != idle_val:
        out_values[5]=in_values[5]+(lr-1500) 
    if ud != idle_val:
        out_values[2]=in_values[2]+(ud-1500) 
    mav1.mav.rc_channels_override_send(mav1.target_system, mav1.target_component, *out_values)


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
    print("Heartbeat from APM (system %u component %u)" % (mav1.target_system, mav1.target_system))
    #set_rcs(1510,1510,1510,1510)


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

if __name__=='__main__':
    init()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        run(),
        ))
    loop.close()
