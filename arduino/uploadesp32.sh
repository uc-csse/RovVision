#!/bin/bash
#ARD_PATH=../../arduino-1.8.5/arduino
ARD_PATH=../../arduino/arduino-1.8.5/arduino

$ARD_PATH --upload --board esp32:esp32:esp32 --port /dev/ttyUSB0 GY-86.ino
