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

##### map radious im meters
rad=20

class CycArr():
    def __init__(self,size=20000):
        self.buf=[]
        self.size=size

    def add(self,arr):
        self.buf.append(arr)
        if len(self.buf)>self.size:
            self.buf.pop(0)

    def get_data(self,label):
        try:
            return np.array([(d['fnum'],*d[label]) for d in self.buf if label in d])
        except:
            return np.array([(d['fnum'],d[label]) for d in self.buf if label in d])

    def __len__(self):
        return len(self.buf)


class Data:
    def reset(self):
        self.md_hist = CycArr(500)

    def __init__(self):
        self.reset()

gdata=Data()

from utils import ab_filt
xf,yf,zf=ab_filt(),ab_filt(),ab_filt()

def update_graph(axes):
    tic=time.time()
    new_data=False
    while 1:
        socks=zmq.select(subs_socks,[],[],0.001)[0]
        if time.time()-tic>=0.09:
            print('too much time break',time.time()-tic())
            break
        if len(socks)==0:
            break
        else:
            for sock in socks:
                ret = sock.recv_multipart()
                topic , data = ret
                data=pickle.loads(ret[1])
                if ret[0]==config.topic_main_telem:
                    gdata.md_hist.add(data)
                    new_data=True
                if ret[0]==config.topic_comp_vis:
                    pass

    if not pause_satus and new_data:
        for i,l in enumerate(pid_labels):
            update_pid(ax_pid_hdls[i],l)
        axes.figure.canvas.draw()

def clear(evt):
    gdata.reset()
    print('reset data')

pause_satus=False
def pause(evt):
    global pause_satus
    pause_satus=not pause_satus
    print('pause=',pause_satus)

def center(evt):
    gdata.map_center = gdata.curr_pos.copy()

def plot_pid(pid_label,grid_size,grid_pos):
    ax=plt.subplot2grid(grid_size, grid_pos)
    plt.title(pid_label)
    hdls=[ax.plot([1],'-b'),ax.plot([1],'-g'),ax.plot([1],'-r')]
    plt.legend(list('pid'),loc='upper left')
    plt.grid('on')
    return (ax,*hdls)

def update_pid(ax_hdls,pid_label):
    xs = np.arange(len(gdata.md_hist))
    ax,hdls = ax_hdls[0],ax_hdls[1:]
    pid_data=gdata.md_hist.get_data(pid_label)
    for i in [0,1,2]:
        hdls[i][0].set_ydata(pid_data[:,i+1])
        hdls[i][0].set_xdata(xs)
    ax.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax.set_ylim(-1,1)




from matplotlib.widgets import Button

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
axcenter = plt.axes([0.59, 0.05, 0.1, 0.075])
axpause = plt.axes([0.7, 0.05, 0.1, 0.075])
axclear = plt.axes([0.81, 0.05, 0.1, 0.075])

timer = fig.canvas.new_timer(interval=50)
timer.add_callback(update_graph, ax)
timer.start()

bnpause = Button(axpause, 'Pause')
bnpause.on_clicked(pause)
bnclear = Button(axclear, 'Clear')
bnclear.on_clicked(clear)
bncenter = Button(axcenter, 'Center')
bncenter.on_clicked(center)

grid_size=(4,1)
pid_labels=['ud_pid','yaw_pid','fb_pid','lr_pid']
ax_pid_hdls=[plot_pid(l,grid_size,(i,0)) for i,l in enumerate(pid_labels)]

plt.show()
