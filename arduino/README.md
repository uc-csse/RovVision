#setup arduino for the imu:

##Hardware
GT-86 from https://www.aliexpress.com/item/GY-86-10DOF-MS5611-HMC5883L-MPU6050-Module-MWC-Flight-Control-Sensor-Module/1986970073.html
arduino promicro from https://www.aliexpress.com/item/Free-Shipping-New-Pro-Micro-for-arduino-ATmega32U4-5V-16MHz-Module-with-2-row-pin-header/2021979132.html

##Software
download arduino 1.6.9
clone https://github.com/jarzebski/Arduino-MS5611.git into arduino-1.6.9/libraries/
clone https://github.com/jrowberg/i2cdevlib.git
copy from i2cdevlib/Arduino the libraries MPU6050,HMC5883L,I2Cdev into arduino-1.6.9/libraries/
copy https://github.com/jrowberg/i2cdevlib/tree/master/Arduino/MPU6050 into arduino-1.6.9/libraries/

##upload arduino
../../arduino/arduino-1.8.5/arduino --upload --board arduino:samd:arduino_zero_native --port /dev/ttyACM0 GT-86.ino
#got the name of the board by:
../../arduino/arduino-1.8.5/arduino --get-pref |grep board
#the samd was taken from the arduino enviroment


#~/arduino-1.6.9$./arduino --upload ../localization_tests/Arduino/GT-86/GT-86.ino




### if you get an error BUFFER_LENGTH not define add BUFFER_LENGTH=32 in the relevant file!!

