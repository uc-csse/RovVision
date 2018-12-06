# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import socket

UDP_IP = "0.0.0.0"
#UDP_IP = "192.168.2.1"
UDP_SRC_PORT = 6600
UDP_DST_PORTS = [5600,6753]

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_SRC_PORT))

#to test gstreamer:
#gst-launch-1.0 -v udpsrc port=6600 ! application/x-rtp,clock-rate=90000,payload=96 ! rtph264depay ! h264parse ! avdec_h264 ! autovideosink

#to save
#gst-launch-1.0 -e -v udpsrc port=6600 ! application/x-rtp, encoding-name=H264, payload=96 ! rtph264depay ! h264parse ! mp4mux ! filesink location=test.mp4
import time
save=True
if save:
    fd=open('test.mp4','wb')
while True:
    data, addr = sock.recvfrom(1024*63)
    if len(data):
        if save:
            fd.write(data)
        for p in UDP_DST_PORTS:
            #time.sleep(0)
            sock.sendto(data,('127.1',p))
