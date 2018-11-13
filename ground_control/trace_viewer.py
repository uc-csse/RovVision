# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import matplotlib.pyplot as plt
import sys,os,time
sys.path.append('../')
import zmq
import pickle
import argparse
import numpy as np
import config
import utils

parser = argparse.ArgumentParser()
args = parser.parse_args()

subs_socks=[]
subs_socks.append(utils.subscribe([config.topic_main_telem,config.topic_comp_vis],config.zmq_local_route))



class CycArr():
    def __init__(self,size=1000):
        self.buf=[]
        self.size=size

    def add(self,arr):
        self.buf.append(arr)
        if len(self.buf)>self.size:
            self.buf.pop(0)

    def __call__(self):
        return np.array(self.buf)

    def __len__(self):
        return len(self.buf)

curr_pos=None
pos_hist = CycArr()
trace_hist = CycArr()
heading_rot = None

def update_graph(axes):
    global hdl_pos,curr_pos,heading_rot
    while 1:
        socks=zmq.select(subs_socks,[],[],0.001)[0]
        if len(socks)==0:
            break
        else:
            for sock in socks:
                ret = sock.recv_multipart()
                topic , data = ret
                data=pickle.loads(ret[1])
                if ret[0]==config.topic_main_telem:
                    if 'heading' in data:
                        #print('---',data['heading'])
                        h = np.radians(data['heading']+90)
                        ch = np.cos(h)
                        sh = np.sin(h)
                        heading_rot = np.array([
                            [   ch,     -sh,    0],
                            [   sh,     ch,     0],
                            [   0,      0,      1]]
                            ) #rotation arround z axis
                if ret[0]==config.topic_comp_vis:
                    if 'trace' in data and heading_rot is not None:
                        t_arr=np.array(data['trace'])
                        trace_hist.add(t_arr)
                        t_arr_r=(heading_rot @ t_arr).flatten()  
                        #import pdb;pdb.set_trace()
                        if curr_pos is None:
                            curr_pos=t_arr_r
                        else:
                            curr_pos+=t_arr_r
                        #print('===',data['fnum'],t_arr_r[0])
                        print('===',data['fnum'],t_arr[1])
                        pos_hist.add(curr_pos.copy())
                        pos_arr=pos_hist()
                        
                        hdl_pos[0].set_ydata(pos_arr[:,1])
                        hdl_pos[0].set_xdata(pos_arr[:,0])
                        trace_arr=trace_hist()

                        xs = np.arange(len(trace_hist)) 
                        for i in [0,1,2]:
                            hdl_trace[i][0].set_xdata(xs)
                            hdl_trace[i][0].set_ydata(trace_hist()[:,i])
                        ax2.set_xlim(len(trace_hist)-100,len(trace_hist))
                        ax2.set_ylim(-0.2*1,0.2*1)
                        
                        rad=20
                        ax1.set_xlim(-rad,rad)
                        ax1.set_ylim(-rad,rad)
            axes.figure.canvas.draw()

def clear():
    pass

def pause():
    pass

from matplotlib.widgets import Button

fig, ax = plt.subplots()
axpause = plt.axes([0.7, 0.05, 0.1, 0.075])
axclear = plt.axes([0.81, 0.05, 0.1, 0.075])


bnpause = Button(axpause, 'Pause')
bnpause.on_clicked(pause)


ax1=plt.subplot2grid((3,2), (0,1),rowspan=3)
hdl_pos = ax1.plot([],[],'.-')
ax2=plt.subplot2grid((3,2), (0,0))
plt.title('trace not oriented')
plt.legend(list('xyz'))
hdl_trace = [ax2.plot([],'-r'),ax2.plot([],'-g'),ax2.plot([],'-b')] 
timer = fig.canvas.new_timer(interval=50)
timer.add_callback(update_graph, ax)
timer.start()



plt.show()
