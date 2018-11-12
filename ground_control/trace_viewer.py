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

curr_pos=None
pos_hist = []
heading_rot = None
def update_graph(axes):
    global hdl,curr_pos,heading_rot
    socks=zmq.select(subs_socks,[],[],0.001)[0]
    if len(socks)>0:
        for sock in socks:
            ret = sock.recv_multipart()
            topic , data = ret
            data=pickle.loads(ret[1])
            if ret[0]==config.topic_main_telem:
                if 'heading' in data:
                    #print('---',data['heading'])
                    h = np.radians(data['heading'])
                    ch = np.cos(h)
                    sh = np.sin(h)
                    heading_rot = np.array([[ch,-sh,0],[sh,ch,0],[0,0,1]])
            if ret[0]==config.topic_comp_vis:
                if 'trace' in data and heading_rot is not None:
                    t_arr=np.array(data['trace'])
                    t_arr=(heading_rot @ t_arr).flatten()  
                    #import pdb;pdb.set_trace()
                    if curr_pos is None:
                        curr_pos=t_arr
                    else:
                        curr_pos+=t_arr
                    print('===',curr_pos)
                    pos_hist.append(curr_pos.copy())
                    pos_arr=np.array(pos_hist)
                    hdl[0].set_ydata(pos_arr[:,1])
                    hdl[0].set_xdata(pos_arr[:,0])

        axes.figure.canvas.draw()


fig, ax = plt.subplots()
hdl = ax.plot([],[],'+')
ax.set_xlim(-1,1)
ax.set_ylim(-1,1)
timer = fig.canvas.new_timer(interval=50)
timer.add_callback(update_graph, ax)
timer.start()





plt.show()
