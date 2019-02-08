# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import config
import zmq
import pickle
import time
import utils


##### to use:
## ipython
## from commands import send
## send(b'yaw_pid.D+=0.03;print(yaw_pid)')

socket_pub = utils.publisher(config.zmq_pub_command)

sock_sub = utils.subscribe([ config.topic_main_command_fb ], config.zmq_pub_main)


def send(cmd):
    socket_pub.send_multipart([config.topic_command,cmd])

def recv(timeoutms=100):
    if sock_sub.poll(timeoutms):
    #if len(zmq.select([sock_sub],[],[],0)[0])>0:
        ret  = sock_sub.recv_multipart()
        return pickle.loads(ret[1])



if __name__=='__main__':
    time.sleep(0.5)
    send(b"tosend='working :)'")
    print(recv())
