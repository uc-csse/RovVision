# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import config
import controller

topic_postition=config.topic_sitl_position_report

context = zmq.Context()
socket_pub = context.socket(zmq.PUB)
socket_sub = context.socket(zmq.SUB)
socket_pub.bind("tcp://*:%d" % config.zmq_pub_drone_main[1] )
socket_sub.connect('tcp://%s:%d'%config.zmq_pub_unreal_proxy)

socket_sub.setsockopt(zmq.SUBSCRIBE,config.topic_unreal_state)


## subscribe to v3d range 
## subscribe to v3d translate
## listen to joystick from gcontrol
## 


if __name__=='__main__':
    while True:
    #    if 
        pass

