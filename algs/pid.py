import numpy as np
import time

class PID(object):
    def __init__(self,P,I,D,limit=0):
        self.P=P
        self.I=I
        self.D=D
        self.i=0 #integrator
        self.current_state=None
        self.prev_state=None
        self.limit=limit
        self.target=None
        self.d=0

    def __call__(self,state,target):
        if self.prev_state is None:
            self.current_state=self.prev_state=state
        self.prev_state=self.current_state
        self.current_state=state
        self.target=target
        self.err=target-state
        self.p=self.err*self.P
        #self.d=-(self.current_state-self.prev_state)*self.D
        d=-(self.current_state-self.prev_state)*self.D
        self.d=self.d*0.7+d*0.3
        self.i+=self.err*self.I
        self.command=self.p+self.d+self.i
        self.command=np.clip(self.command,-self.limit,self.limit)
        return self.command 
         
    def __str__(self):
        line='PID:{:.2f},{:.2f},{:.2f} err={:.2f} target={:.2f} pid:{:.2f},{:.2f},{:.2f}'
        return line.format(self.P,self.I,self.D,self.err,self.target,self.p,self.i,self.d)

if __name__=='__main__':
    import pylab
    state = 0 
    target = 1.0
    pid=PID(0.2,0.001,0.2,0.1)
    err=[]
    p=[]
    i=[]
    d=[]
    c=[]
    for _ in range(100):
        cmd=pid(state,target)
        err.append(pid.err)
        p.append(pid.p)
        i.append(pid.i)
        d.append(pid.d)
        c.append(pid.command)

        state+=cmd
        print(str(pid))
    pylab.plot(err)
    pylab.plot(p)
    pylab.plot(i)
    pylab.plot(d)
    pylab.plot(c)
    pylab.legend(['err','p','i','d','cmd'])
    pylab.show()




