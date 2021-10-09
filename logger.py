import serial_wrapper
import redcap
import time

swanSer = None
nirsSer = None

while True:
    if(swanSer == None):
        swanSer = serial_wrapper.connect_swan()
        if(swanSer == None):
            time.sleep(5)
    else:
        swanLine = serial_wrapper.read_swan(swanSer)
        if(swanLine == None):
            swanLine.close()
            swanSer = None
            time.sleep(2)

    if(nirsSer == None):
        nirsSer = serial_wrapper.connect_nirs()
        if(nirsSer == None):
            time.sleep(5)
    else:
        nirsLine = serial_wrapper.read_nirs(nirsSer) 
        if(nirsLine == None): 
            nirsSer.close()
            nirsSer = None
            time.sleep(2)
        else:
            print(nirsLine)


