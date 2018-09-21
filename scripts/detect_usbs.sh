ESP_USB=`dmesg |sort -r |grep ch341-uart |grep 'attached to ttyUSB' | head -n 1 | awk '{print $NF}'`
SERIAL_USB=`dmesg |sort -r |grep cp210x |grep 'attached to ttyUSB' | head -n 1 | awk '{print $NF}'`
