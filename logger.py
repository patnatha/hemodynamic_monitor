import serial_wrapper
import redcap

swanSer = None

while True:
    if(swanSer == None):
        swanSer = serial_wrapper.connect_swan()
    else:
        print(serial_wrapper.read_swan(swanSer))
        
