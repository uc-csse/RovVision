# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import zmq
import numpy as np
context = zmq.Context()

def subscribe(topics,port,ip='127.0.0.1'):
    zmq_sub = context.socket(zmq.SUB)
    zmq_sub.connect("tcp://%s:%d" % (ip,port))
    for topic in topics:
        zmq_sub.setsockopt(zmq.SUBSCRIBE,topic)
    return zmq_sub

def publisher(port,ip='127.0.0.1'): 
    socket_pub = context.socket(zmq.PUB)
    socket_pub.bind("tcp://%s:%d" % (ip,port) )
    return socket_pub



class  avg_win_filt():
    def __init__(self,size):
        self.size=size
        self.buf=[]
    def __call__(self,val):
        self.buf.append(val)
        if len(self.buf)>self.size:
            self.buf.pop(0)
        return np.mean(self.buf)

    def reset(self):
        self.buf=[]

