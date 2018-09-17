# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import zmq
context = zmq.Context()

def subscribe(topics,port,ip='127.0.0.1'):
    zmq_sub = context.socket(zmq.SUB)
    zmq_sub.connect("tcp://%s:%d" % (ip,port))
    for topic in topics:
        zmq_sub.setsockopt(zmq.SUBSCRIBE,topic)
    return zmq_sub

def publisher(port,ip='127.0.0.1'): 
    socket_pub = context.socket(zmq.PUB)
    socket_pub.bind("tcp://%s:%d" % (ip,port) )
    return socket_pub
