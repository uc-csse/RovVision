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

from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


class kal_filt():
    def __init__(self,x=[0,0]):
        self.reset(x)

    def reset(self,x):
        f = KalmanFilter (dim_x=2, dim_z=1)
        f.x = np.array([[x[0]],[x[1]]])
        f.F = np.array([[1.0,1.0] , [0.0, 1.0]])
        f.H = np.array([[1.,0.]])
        f.P=np.eye(2)*0.001 #eye * cov matrix #process noise
        f.R=np.array([[0.05]]) #mesurment noise 
        f.Q = Q_discrete_white_noise(dim=2, dt=0.1, var=0.03)
        self.f=f

    def __call__(self,val):
        self.f.predict()
        self.f.update(val)
        return self.f.x[0][0],self.f.x[1][0]


if __name__=='__main__':
    kf=kal_filt()
    for i in range(100):
        rval=float(i)+np.random.random(1)[0]*i-0.5
        print(i,rval,kf(rval),kf.f.Q[0,0])



