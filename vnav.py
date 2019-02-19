from vnpy import *
import time
import os
s=EzAsyncData.connect('/dev/'+os.environ['VNAV_USB'],115200)
s.sensor.write_async_data_output_frequency(40) #hz
def get_data():
    cd=s.current_data
    ret={}
    ypr=cd.yaw_pitch_roll
    rates=cd.angular_rate
    #acc=cd.acceleration
    ret['ypr']=(ypr.x,ypr.y,ypr.z)
    ret['rates']=(rates.x,rates.y,rates.z)
    return ret
