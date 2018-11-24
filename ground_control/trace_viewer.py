# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import matplotlib.pyplot as plt
import sys,os,time
sys.path.append('../')
sys.path.append('../algs')
import zmq
import pickle
import argparse
import numpy as np
import config
import utils
from camera_tools import get_stereo_cameras,triangulate


parser = argparse.ArgumentParser()
args = parser.parse_args()

subs_socks=[]
subs_socks.append(utils.subscribe([config.topic_main_telem,config.topic_comp_vis],config.zmq_local_route))

def generate_stereo_cameras():
    return get_stereo_cameras(config.focal_length,(config.pixelwidthy,config.pixelwidthx),config.baseline,config.camera_pitch)

def calc_trace(prev_pts,cur_pts,yaw_delta_mat):
    caml,camr=generate_stereo_cameras()

    pt_l_x,pt_l_y,pt_r_x,pt_r_y = prev_pts
    t_pt1 = triangulate(caml,camr,pt_l_x,pt_l_y,pt_r_x,pt_r_y)
    pt_l_x,pt_l_y,pt_r_x,pt_r_y = cur_pts
    #t_pt2 = triangulate(yaw_delta_mat.T @ caml ,yaw_delta_mat.T @ camr,pt_l_x,pt_l_y,pt_r_x,pt_r_y)
    t_pt2 = triangulate(caml @ yaw_delta_mat , camr @ yaw_delta_mat ,pt_l_x ,pt_l_y,pt_r_x,pt_r_y)
    #t_pt2 = triangulate( caml , camr,pt_l_x,pt_l_y,pt_r_x,pt_r_y)
    return np.array(t_pt2)-np.array(t_pt1)
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

    def __call__(self):
        return np.array(self.buf)

    def __len__(self):
        return len(self.buf)


class Data:
    def reset(self):
        self.curr_pos=None
        self.pos_hist = CycArr()
        self.trace_hist = CycArr(500)
        self.heading_rot = None
        self.map_center = (0,0)
        self.range_arr = CycArr(500)
        self.prev_pts = None
        self.last_ref = -1

    def __init__(self):
        self.reset()

gdata=Data()

from utils import ab_filt
xf,yf,zf=ab_filt(),ab_filt(),ab_filt()

ch,sh=0,0
def update_graph(axes):
    global hdl_pos,hdl_arrow,ch,sh
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
                    if 'yaw' in data:
                        #print('---',data['heading']+90,data['yaw']/np.pi*180+90)
                        h = (data['yawspeed']/config.fps)
                        ch = np.cos(h)
                        sh = np.sin(h)
                        gdata.heading_speed = np.array([
                            [   ch,     -sh,    0,  0],
                            [   sh,     ch,     0,  0],
                            [   0,      0,      1,  0],
                            [   0,      0,      0,  1]]
                            ) #rotation arround z axis
                        h = -(data['yaw']+np.pi/2)
                        ch = np.cos(h)
                        sh = np.sin(h)
                        gdata.heading_rot = np.array([
                            [   ch,     -sh,    0],
                            [   sh,     ch,     0],
                            [   0,      0,      1]]
                            ) #rotation arround z axis
                if ret[0]==config.topic_comp_vis:
                    if 'range_z' in data:
                        gdata.range_arr.add(-data['range_z'])

                    if gdata.heading_rot is not None:
                        pts=(*data['pt_l'],*data['pt_r'])
                        if gdata.prev_pts is None:
                            gdata.prev_pts = pts
                            gdata.last_ref = data['ref_cnt']
                        else:
                            if data['ref_cnt'] == gdata.last_ref:
                                new_data=True
                                t_arr = calc_trace(gdata.prev_pts,pts,gdata.heading_speed)
                                #t_arr=np.array(data['trace'])
                                x,y,z=t_arr
                                #print('-- '+('{:.3f} '*3).format(x,y,z))
                                tr=0.3
                                if abs(x)>tr or  abs(y)>tr or abs(z)>tr:
                                    print('error too big movement',x,y,z)
                                    x,y,z = (0,0,0)
                                t_arr = (xf(x)[0],yf(y)[0],zf(z)[0])
                                gdata.trace_hist.add(t_arr)
                                t_arr_r=(gdata.heading_rot @ t_arr).flatten()
                                #import pdb;pdb.set_trace()
                                if gdata.curr_pos is None:
                                    gdata.curr_pos=t_arr_r
                                else:
                                    gdata.curr_pos+=t_arr_r
                                #print('===',data['fnum'],t_arr_r[0])
                                #print('===',data['fnum'],t_arr[1])
                                gdata.pos_hist.add(gdata.curr_pos.copy())
                                pos_arr=gdata.pos_hist()
                                trace_arr=gdata.trace_hist()
                            gdata.prev_pts=pts
                            gdata.last_ref = data['ref_cnt']

    if not pause_satus and new_data:
        xs = np.arange(len(gdata.trace_hist))
        hdl_pos[0].set_ydata(pos_arr[:,1])
        hdl_pos[0].set_xdata(pos_arr[:,0])
        #hdl_last_pos
        for i in [0,1,2]:
            hdl_trace[i][0].set_xdata(xs)
            hdl_trace[i][0].set_ydata(gdata.trace_hist()[:,i])
        ax2.set_xlim(len(gdata.trace_hist)-100,len(gdata.trace_hist))
        ax2.set_ylim(-0.2*4,0.2*4)
        hdl_arrow.remove()
        hdl_arrow = ax1.arrow(gdata.curr_pos[0],gdata.curr_pos[1],-ch*0.1,-sh*0.1,width=0.3)

        cx,cy = gdata.map_center[:2]
        ax1.set_xlim(-rad+cx,rad+cx)
        ax1.set_ylim(-rad+cy,rad+cy)

        xs = np.arange(len(gdata.range_arr))
        hdl_range[0][0].set_xdata(xs)
        #print(pos_arr[:,2][-3:])
        hdl_range[0][0].set_ydata(gdata.range_arr.buf)
        ax3.set_xlim(len(xs)-100,len(xs))
        ax3.set_ylim(0,2)

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

from matplotlib.widgets import Button

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
axcenter = plt.axes([0.59, 0.05, 0.1, 0.075])
axpause = plt.axes([0.7, 0.05, 0.1, 0.075])
axclear = plt.axes([0.81, 0.05, 0.1, 0.075])




ax1=plt.subplot2grid((3,2), (0,1),rowspan=3)
hdl_pos = ax1.plot([1,2],[1,2],'-')
hdl_arrow = ax1.arrow(1,1,0.5,0.5,width=0.1)

ax2=plt.subplot2grid((3,2), (0,0))
plt.title('trace not oriented')
plt.legend(list('xyz'))
hdl_trace = [ax2.plot([1],'-r'),ax2.plot([1],'-g'),ax2.plot([1],'-b')]

ax3=plt.subplot2grid((3,2), (1,0))
plt.title('ground range')
hdl_range  = [ax3.plot([1],'-')]
plt.grid('on')



timer = fig.canvas.new_timer(interval=50)
timer.add_callback(update_graph, ax)
timer.start()


bnpause = Button(axpause, 'Pause')
bnpause.on_clicked(pause)
bnclear = Button(axclear, 'Clear')
bnclear.on_clicked(clear)
bncenter = Button(axcenter, 'Center')
bncenter.on_clicked(center)

plt.show()
