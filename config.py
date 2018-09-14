# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#pubsub
zmq_pub_drone_fdm=('127.0.0.1',5566)
#zmq_pub_drone_fdm=('127.0.0.1',12466)
topic_sitl_position_report=b'position_rep'

zmq_pub_unreal_proxy=('127.0.0.1',5577)
topic_unreal_state=b'unreal_state'
topic_unreal_drone_rgb_camera=b'rgb_camera_%d'

zmq_pub_comp_vis = 8877 #only port
topic_comp_vis = b'comp_vis'
zmq_pub_comp_vis_imgs = 8878

n_drones = 1


zmq_pub_joy=9117
topic_button = b'topic_button'
topic_axes = b'topic_axes'

zmq_pub_main=9921
topic_main_telem=b'topic_main_telem'


#currently need to be changed also in ssh_route.sh
gst_ports=[6760,6761]


zmq_pub_imu=9217
topic_imu=b'topic_imu'
