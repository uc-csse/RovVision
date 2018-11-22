# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import config
import zmq

import utils


##### to use:
## ipython
## from commands import send
## send(b'yaw_pid.D+=0.03;print(yaw_pid)')

socket_pub = utils.publisher(config.zmq_pub_command)

def send(cmd):
    socket_pub.send_multipart([config.topic_command,cmd])


