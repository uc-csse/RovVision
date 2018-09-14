# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from pymavlink import mavutil
import numpy as np
import zmq
import sys,os
import time
import pickle
#import config
import asyncio


mav1 = None
event = None
__pos = None

#chan 3 up/down (right fwd/bck)
#chan 4 yaw (right right/left)
#chan 5 fwd/back  (left fwd,back)
#chan 6 lef/right (left left,right)



def get_pos():
    return __pos

def set_rcs(ud, yaw, fb, lr):
    global mav1
    values = [ 1500 ] * 8
    values[2] = ud
    values[3] = yaw
    values[4] = fb
    values[5] = lr
    mav1.mav.rc_channels_override_send(mav1.target_system, mav1.target_component, *values)


def get_position_struct(mav):
    d={}
    if 'VFR_HUD' in mav1.messages:
        d['posz']=mav1.messages['VFR_HUD'].alt
    if 'SIMSTATE' in mav1.messages:
        sm=mav1.messages['SIMSTATE']
        d['yaw']=np.degrees(sm.yaw)
        d['roll']=np.degrees(sm.roll)
        d['pitch']=np.degrees(sm.pitch)
    if {'SIMSTATE','HOME'} in set(mav1.messages):
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


async def run():
    global mav1,event,__pos
    while True:
        time.sleep(0)
        mav1.recv_msg()
        __pos=get_position_struct(mav1)
        if __pos  and event is not None and event.trigger():
            #print(mav1.messages['VFR_HUD'].alt)
            #print(mav1.messages.keys())
            #print(mav1.messages['HOME'])
            #print(mav1.messages['SIMSTATE'])
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
