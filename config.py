# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import os
#pubsub
#zmq_pub_drone_fdm=('127.0.0.1',5566)
#zmq_pub_drone_fdm=('127.0.0.1',12466)
topic_sitl_position_report=b'position_rep'

zmq_pub_unreal_proxy=5577

topic_unreal_state=b'unreal_state'
topic_unreal_drone_rgb_camera=b'rgb_camera_%d'

zmq_pub_comp_vis = 8877 #only port
topic_comp_vis = b'comp_vis'
topic_comp_vis_cmd = b'comp_vis_cmd'
zmq_pub_comp_vis_imgs = 8878

n_drones = 1


zmq_pub_joy=9117
### joystick topics
topic_button = b'topic_button'
topic_axes = b'topic_axes'
topic_hat = b'topic_hat'

zmq_pub_main=9921
topic_main_telem=b'topic_main_telem'
topic_mav_telem=b'topic_mav_telem'


#currently need to be changed also in ssh_route.sh
gst_ports=[6760,6761]


zmq_pub_imu=9217
topic_imu=b'topic_imu'

#joystick mapping
joy_save = 8
joy_toggle_laser1 = 1
joy_init_track = 5
joy_arm = 7
joy_disarm = 6
joy_manual = 0
joy_depth_hold = 3

#camera params
fps = 10

#camera info estimate
fov=60.97
pixelwidthx = 640 #after shrink
pixelwidthy = 512 #after shrink
baseline = 0.14 # (240-100)*.1scale in cm from unreal engine
focal_length=pixelwidthx/( np.tan(np.deg2rad(fov/2)) *2 )
#disparity=x-x'=baseline*focal_length/Z
#=>> Z = baseline*focal_length/disparity 
if 'SIMROV' in os.environ:
    track_offx=30
    track_params = (30,30,60,60,track_offx,0) 
    stereo_corr_params = {'ws':(80,80),'sxl':250+50,'sxr':0,'ofx':50}

    scl=20
    ud_params=(0.5*scl,0.005*scl,0.5*scl,0.3*scl)
else:
    track_offx=0#100
    track_offx=70
    track_params = (30,30,40,40,track_offx,0) 
    #stereo_corr_params = {'ws':(80,80),'sxl':250,'sxr':0,'ofx':150}
    #stereo_corr_params = {'ws':(80,80),'sxl':250,'sxr':0,'ofx':70}
    stereo_corr_params = {'ws':(80,80),'sxl':250+50,'sxr':0,'ofx':70}

############## control
lr_filt_size = 1
default_js_gain=0.6
## pids
_gs=1.0/1000/default_js_gain #convert back to pwm factor
if 'SIMROV' in os.environ:
    scl=20
    ud_params=(0.5*scl,0.005*scl,0.5*scl, _gs*500 ,0.0, _gs * 150)
    scl=6
    lr_params=(1.02*scl,0.002*scl,4.6*scl, _gs*400 , 0 , _gs * 150) 
    scl=6
    fb_params=(0.42*scl,0.002*scl,1.0*scl, _gs*400 ,0.0, _gs * 100)
else:
    scl=20
    ud_params=(0.5*scl,0.005*scl,0.5*scl,0.3*scl)
    scl=6
    lr_params=(2.02*scl,0.10*scl,4.6*scl,6.4*scl, 0, _gs * 150) 
    scl=12
    fb_params=(0.12*scl,0.002*scl,1.0*scl,6.4*scl, 0, _gs * 150)

