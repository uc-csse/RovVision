# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import serial,sys,time
import argparse

#https://github.com/espressif/esptool/wiki/ESP32-Boot-Mode-Selection
if 1 and __name__=="__main__":
    parser = argparse.ArgumentParser(description='''
To reset the esp32:
python send_byte.py -d 0
''')
    parser.add_argument("-s","--send", help="bytes to send in hex format eg 0101 for two bytes")
    parser.add_argument("-d","--dtr",help="sets value 0 or 1 to DTR line in esp32 its GPIO0") 
    parser.add_argument("-r","--rts",help="sets value 0 or 1 to RTS line in esp32 its EN") 
    parser.add_argument("-b","--baudrate",help="sets baudrate default 512000",default="460800")
    parser.add_argument("-u","--usbdevice",help="sets usbdevice default /dev/ttyUSB0",default='/dev/ttyUSB0')
    args = parser.parse_args()
#import pdb;pdb.set_trace()
ser = serial.Serial(args.usbdevice,baudrate=int(args.baudrate), rtscts=True, dsrdtr=True)
if args.send is not None:
    tosend = b'%c'%int(args.send,16)
    print('sending ...',tosend)
    ser.write(tosend)
    #print(ser.read(1))
    ser.flush()
if  args.rts is not None:
    ser.rts=int(args.rts)
if  args.dtr is not None:
    ser.dtr=int(args.dtr)

time.sleep(1)
#if ser.inWaiting()>0:
#    print(ser.read())
ser.close()
