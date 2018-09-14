#!/bin/bash
#ARD_PATH=../../arduino-1.8.5/arduino
ARD_PATH=../../arduino/arduino-1.8.5/arduino

$ARD_PATH --upload --board esp8266:esp8266:nodemcuv2 --port /dev/ttyUSB0 GT-86.ino
