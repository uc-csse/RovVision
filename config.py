# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import os

camera_pitch = np.radians(0) # camera installation pitch in rad
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

zmq_pub_command=9931
topic_command=b'topic_command'


zmq_local_route=10921

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

class Joy_map:
    ud=4
    yaw=3
    fb=1
    lr=0
#camera params
fps = 10

#camera info estimate
fov=60.97
pixelwidthx = 640 #after shrink
pixelwidthy = 512 #after shrink
baseline = 0.14 # (240-100)*.1scale in cm from unreal engine
focal_length=pixelwidthx/( np.tan(np.deg2rad(fov/2)) *2 )
#camera_pitch = np.radians(45) # camera installation pitch in rad

#disparity=x-x'=baseline*focal_length/Z
#=>> Z = baseline*focal_length/disparity
if 'SIMROV' in os.environ:
    track_offx=80
    track_params = (60,60,60,60,track_offx,0)
    stereo_corr_params = {'ws':(80,80),'sxl':250+50,'sxr':0,'ofx':80}

    scl=20
    ud_params=(0.5*scl,0.005*scl,0.5*scl,0.3*scl)
else:
    #track_offx=0#100
    track_offx=80
    track_params = (60,60,60,60,track_offx,0)
    #stereo_corr_params = {'ws':(80,80),'sxl':250,'sxr':0,'ofx':150}
    #stereo_corr_params = {'ws':(80,80),'sxl':250,'sxr':0,'ofx':70}
    stereo_corr_params = {'ws':(80,80),'sxl':250+50,'sxr':0,'ofx':80}

############## control
lr_filt_size = 1
default_js_gain=0.6
## pids
_gs=1.0/1000/default_js_gain #convert back to pwm factor

### args: P,I,D,limit,step_limit,i_limit,FF,is angle=0
if 'SIMROV' in os.environ:
    scl=1
    ud_update_scale=5.0
    ud_params_k = {'initial_i':0.07}
    ud_params=(0.15,0.001,1.5, _gs*300 , _gs * 100, _gs*200, 0.2, False)
    scl=2
    lr_params=(0.62*scl,0.002*scl,3.0*scl, _gs*400 , _gs * 150, _gs*200, 0, False)
    scl=2
    fb_params=(0.42*scl,0.002*scl,2.0*scl, _gs*400 , _gs * 100, _gs*200, 0, False)
    scl=0.03
    yaw_update_scale=1.0
    yaw_params=(0.2*scl,0.000*scl,4.8*scl, _gs*400 , _gs * 250, _gs*100, 0.5, True)
else:
    scl=6
    ud_update_scale=5.0
    ud_params_k = {'initial_i':0.07}
    ud_params=(0.15,0.002,1.5, _gs*500 , _gs * 150, _gs*200, 0.1, False)
    scl=6
    lr_params=(0.2*scl,0.002*scl,0.2*scl, _gs*500 , _gs * 150, _gs*200, 0, False)
    scl=6
    fb_params=(0.2*scl,0.002*scl,0.2*scl, _gs*500 , _gs * 150, _gs*200, 0, False)
    scl=0.02
    yaw_update_scale=1.0
    yaw_params=(0.2*scl,0.000*scl,4.8*scl, _gs*400 , _gs * 250, _gs*100, 0.5, True)
