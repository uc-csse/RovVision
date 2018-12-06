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
parser.add_argument("--ud",help="ud pid plot", action='store_true')
parser.add_argument("--yaw",help="yaw pid plot", action='store_true')
parser.add_argument("--fb",help="fb pid plot", action='store_true')
parser.add_argument("--lr",help="lr pid plot", action='store_true')
parser.add_argument("--roll",help="roll data", action='store_true')
parser.add_argument("--pitch",help="pitch data", action='store_true')
parser.add_argument("--depth",help="depth info", action='store_true')
args = parser.parse_args()

grid_h = sum([(1 if a else 0)*2 for a in (args.ud,args.yaw,args.fb,args.lr)])
if args.depth:
    grid_h+=1
if args.roll:
    grid_h+=1
if args.pitch:
    grid_h+=1

print('grid_h',grid_h)
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
        self.vd_hist = CycArr(500)

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
                    gdata.vd_hist.add(data)


    if not pause_satus and new_data:
        for i,l in enumerate(labels):
            update_pid(ax_pid_hdls[i],l)
        if args.depth:
            update_deapth_range(depth_hdls)
        if args.roll:
            update_roll(roll_hdls)
        if args.pitch:
            update_pitch(pitch_hdls)
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


def update_pitch(ax_hdls):
    return update_pitch_roll(ax_hdls,['pitch','fb_cmd'])
def update_roll(ax_hdls):
    return update_pitch_roll(ax_hdls,['roll','lr_cmd'])

def update_pitch_roll(ax_hdls,labels):
    ax1,ax2 = ax_hdls[0]
    hdl_r,hdl_cr = ax_hdls[1]
    xs = np.arange(len(gdata.md_hist))
    roll=gdata.md_hist.get_data(labels[0])
    command_roll=gdata.md_hist.get_data(labels[1])
    #print('lock_range_data',lock_range_data[-1,:])
    hdl_r[0].set_ydata(-roll[:,1]/np.pi*180.0)
    hdl_r[0].set_xdata(xs)
    hdl_cr[0].set_ydata(-command_roll[:,1])
    hdl_cr[0].set_xdata(xs)
    ax1.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax1.set_ylim(-40,40)
    ax2.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax2.set_ylim(-500,500)

def plot_roll_pitch(grid_size,grid_pos,labels):
    ax1=plt.subplot2grid(grid_size, (grid_pos,0))
    plt.title(labels[0])
    hdl_r=ax1.plot([1],'-g') #deapth
    plt.legend([labels[0]],loc='upper left')
    ax2 = ax1.twinx()
    hdl_cr=ax2.plot([1],'-r') #range
    plt.legend([labels[1]],loc='lower left')
    return (ax1,ax2),(hdl_r,hdl_cr)

def plot_roll(grid_size,grid_pos):
    return plot_roll_pitch(grid_size,grid_pos,['roll','lr_cmd'])
def plot_pitch(grid_size,grid_pos):
    return plot_roll_pitch(grid_size,grid_pos,['pitch','fb_cmd'])


def plot_deapth_range(grid_size,grid_pos):
    ax1=plt.subplot2grid(grid_size, (grid_pos,0))
    plt.title('deapth range')
    hdl_d=ax1.plot([1],'-g') #deapth
    ax2 = ax1.twinx()
    hdl_r=ax2.plot([1],'-r') #range
    hdl_lr=ax2.plot([1],'-b') #lock_range
    plt.legend(['lock_range','ground range'],loc='upper left')
    return (ax1,ax2),(hdl_d,hdl_r,hdl_lr)

def update_deapth_range(ax_hdls):
    ax1,ax2 = ax_hdls[0]
    hdl_d,hdl_r,hdl_lr = ax_hdls[1]
    xs = np.arange(len(gdata.md_hist))
    lock_range_data=gdata.md_hist.get_data('lock_yaw_depth')
    depth_data=gdata.md_hist.get_data('depth')
    #print('lock_range_data',lock_range_data[-1,:])
    hdl_d[0].set_ydata(-depth_data[:,1])
    hdl_d[0].set_xdata(xs)
    hdl_lr[0].set_ydata(-lock_range_data[:,3])
    hdl_lr[0].set_xdata(xs)
    hdl_r[0].set_ydata(lock_range_data[:,4])
    hdl_r[0].set_xdata(xs)
    ax1.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax1.set_ylim(-2,0)
    ax2.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax2.set_ylim(-2,0)

def plot_pid(pid_label,grid_size,grid_pos):
    ax=plt.subplot2grid(grid_size, (grid_pos,0))
    plt.title(pid_label)
    hdls=[ax.plot([1],'-b'),ax.plot([1],'-g'),ax.plot([1],'-r')]
    plt.legend(list('pid'),loc='upper left')
    plt.grid('on')

    ax2=plt.subplot2grid(grid_size, (grid_pos+1,0))
    plt.title(pid_label + ' cmd')
    hdls2=[ax2.plot([1],'-b')]#,ax.plot([1],'-g'),ax.plot([1],'-r')]
    plt.legend(list('ced'),loc='upper left')
    plt.grid('on')


    return ((ax,*hdls),(ax2,*hdls2))

def update_pid(ax_hdls,label):
    xs = np.arange(len(gdata.md_hist))
    ax,hdls = ax_hdls[0][0],ax_hdls[0][1:]
    pid_data=gdata.md_hist.get_data(label+'_pid')
    for i in [0,1,2]:
        hdls[i][0].set_ydata(pid_data[:,i+1])
        hdls[i][0].set_xdata(xs)
    ax.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax.set_ylim(-1,1)

    ax2,hdls2 = ax_hdls[1][0],ax_hdls[1][1:]
    cmd_data=gdata.md_hist.get_data(label+'_cmd')
    hdls2[0][0].set_xdata(xs)
    hdls2[0][0].set_ydata(cmd_data[:,1])
    ax2.set_xlim(len(gdata.md_hist)-400,len(gdata.md_hist))
    ax2.set_ylim(-300,300)

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

grid_size=(grid_h,1)
labels=[a for a in ['ud','yaw','fb','lr'] if eval('args.'+a)]
ax_pid_hdls=[plot_pid(l,grid_size,i*2) for i,l in enumerate(labels)]
curr_grids = len(labels)*2

if args.depth:
    depth_hdls = plot_deapth_range(grid_size,curr_grids)
    curr_grids+=1

if args.roll:
    roll_hdls = plot_roll(grid_size,curr_grids)
    curr_grids+=1
if args.pitch:
    pitch_hdls = plot_pitch(grid_size,curr_grids)
    curr_grids+=1

plt.show()
