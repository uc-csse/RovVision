# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import config
import controller
import zmq
import asyncio
import pickle
import time
from algs import pid

topic_postition=config.topic_sitl_position_report

context = zmq.Context()
zmq_sub_joy = context.socket(zmq.SUB)
zmq_sub_joy.connect("tcp://127.0.0.1:%d" % config.zmq_pub_joy)
zmq_sub_joy.setsockopt(zmq.SUBSCRIBE,config.topic_button)

zmq_sub_v3d = context.socket(zmq.SUB)
zmq_sub_v3d.connect("tcp://127.0.0.1:%d" % config.zmq_pub_comp_vis)
zmq_sub_v3d.setsockopt(zmq.SUBSCRIBE,config.topic_comp_vis)


socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://127.0.0.1:%d" % config.zmq_pub_main )



## system states 
lock_state=False
lock_range=None
track_info = None

async def get_zmq_events():
    global lock_state,track_info, lock_range
    while True:
        socks=zmq.select([zmq_sub_joy,zmq_sub_v3d],[],[],0)[0]
        for sock in socks:
            ret  = sock.recv_multipart()
            if ret[0]==config.topic_button:
                data=pickle.loads(ret[1])
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
            if ret[0]==config.topic_comp_vis:
                track_info=pickle.loads(ret[1])
                #print('-------------topic',track_info)
        await asyncio.sleep(0.001) 

start = time.time()
async def control():
    global lock_state,track_info

    ### y
    ud_params=(0.5,0.005,0.5,0.3)
    ud_pid=pid.PID(*ud_params)
    
    ### x
    lr_params=(0.2,0.001,0.2,0.2)
    lr_pid=pid.PID(*lr_params)
    
    ### range
    fb_params=(0.2,0.001,0.2,0.2)
    fb_pid=pid.PID(*fb_params)

    ud_cmd,lr_cmd,fb_cmd = 1500,1500,1500


    telem={}
    while 1:
        if track_info is not None and lock_state:
            if 'dy' in track_info: 
                ud_cmd = ud_pid(track_info['dy'],0)
                ud_cmd=int(ud_cmd*2000+1500)
            else:
                ud_pid=pid.PID(*ud_params)
                #ud_cmd=1500
            
            if 'dx' in track_info: 
                lr_cmd = lr_pid(track_info['dx'],0)
                lr_cmd=int(-lr_cmd*500+1500)
            else:
                lr_pid=pid.PID(*lr_params)
                #lr_cmd=1500

            range_key = 'range_avg'

            if range_key in track_info: 
                fb_cmd = fb_pid(track_info[range_key],lock_range)
                print('C {:>5.3f} P {:>5.3f} I {:>5.3f} D {:>5.3f}'.format(fb_cmd,fb_pid.p,fb_pid.i,fb_pid.d))
                fb_cmd=int(-fb_cmd*500+1500)
            else:
                fb_pid=pid.PID(*fb_params)
            #print('-----------',ud_cmd,lr_cmd,fb_cmd,lock_range)
            telem.update({'ud_cmd':ud_cmd,'lr_cmd':lr_cmd,'fb_cmd':fb_cmd,'lock_range':lock_range})
            track_info = None
            controller.set_rcs(ud_cmd,1500,fb_cmd,lr_cmd)
        
        telem.update({'ts':time.time()-start, 'lock':lock_state}) 
        socket_pub.send_multipart([config.topic_main_telem,pickle.dumps(telem,-1)]) 

        await asyncio.sleep(0.1)#~10hz control 


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

