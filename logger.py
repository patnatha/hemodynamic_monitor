import serial_wrapper
from serial_wrapper import NIRS, VIGILENCE, HEMOSPHERE, BAUDRATE
import redcap
from redcap import convert_int, convert_one_decimal
import time
import threading
from datetime import datetime

#This the list for collating centrally and is shared between threads
queueLock = threading.Lock()
queue = []

#This is the list of used ports shared between threads
conPorts = {}
conPortLock = threading.Lock()

def swanReading():
    swanSer = None
    while True:
        if(swanSer == None):
            #Get the port lock
            conPortLock.acquire() 

            #Try and connect to Swan
            swanSer = serial_wrapper.connect_swan(conPorts)
            
            #Set this port as used
            if(swanSer != None):
                conPorts[HEMOSPHERE] = swanSer.port
                conPorts[VIGILENCE] = swanSer.port
            else:
                #If not port available wait 5 seconds
                time.sleep(5)

            #Release the port lock
            conPortLock.release()
        else:
            #Read a swan line
            swanLine = serial_wrapper.read_swan(swanSer)
            if(swanLine == None):
                #Close the serial port
                swanSer.close()
                swanSer = None

                #Release this port
                conPortLock.acquire()
                conPorts[VIGILENCE] = None
                conPorts[HEMOSPHERE] = None
                conPortLock.release()
            else:
                #Push this datapoint into the list buffer
                queueLock.acquire()
                queue.append(swanLine)
                queueLock.release()

def nirsReading():
    nirsSer = None
    while True:
        if(nirsSer == None):
            #Get the port lock
            conPortLock.acquire()

            #Try and connect to NIRS
            nirsSer = serial_wrapper.connect_nirs(conPorts)
            
            #Set this port as used
            if(nirsSer != None):
                conPorts[NIRS] = nirsSer.port
            else:
                #If no port available wait 5 seconds
                time.sleep(5)

            #Release the lock
            conPortLock.release()
        else:
            #Read the nirs line
            nirsLine = serial_wrapper.read_nirs(nirsSer) 
            if(nirsLine == None): 
                #Close the serial port
                nirsSer.close()
                nirsSer = None

                #Release this port
                conPortLock.acquire()
                conPorts[NIRS] = None
                conPortLock.release()
            else:
                #Push the datapoint into the list buffer
                queueLock.acquire()
                queue.append(nirsLine)
                queueLock.release()

swanThread = None
nirsThread = None
while True:
    if(swanThread == None):
        swanThread = threading.Thread(target=swanReading, args=(), daemon=True)
        swanThread.start()

    if(nirsThread == None):
        nirsThread = threading.Thread(target=nirsReading, args=(), daemon=True)
        nirsThread.start()

    #Sleep for two seconds 
    time.sleep(2)
   
    #List variable for snending
    toSend = []
    
    #Lock the queue
    queueLock.acquire()

    #ITerate through all items in the queue
    numOfElem = len(queue)
    for i in range(0,numOfElem):
        #Pop the first item in the queue
        item = queue.pop(0)

        if((datetime.now() - item['datetime']).seconds > 4):
            #Process item if greater than 5 seconds in the past
            toSend.append(item)
        else:
            #Requeue the item if too recent
            queue.append(item)
    
    #Release the queue lock
    queueLock.release()

    #Process the item
    for item in toSend:
        #Build the translation struct to red cap
        theStruct = {}
        theStruct['name'] = item['datetime'].strftime("%Y-%m-%d")
        theStruct['datetime'] = item['datetime'].strftime("%Y-%m-%d %H:%M:%S")
        theStruct['temperature'] = convert_one_decimal(item['temp'])
        theStruct['cardiac_output'] = convert_one_decimal(item['CO'])
        theStruct['cardiac_output_stat'] = convert_one_decimal(item['CO_STAT'])
        theStruct['end_diastolic_volume'] = convert_int(item['EDV'])
        theStruct['rv_ejection_fraction'] = convert_int(item['RVEF'])
        theStruct['stroke_volume'] = convert_int(item['SV'])
        theStruct['svo2'] = convert_int(item['SVO2'])
        theStruct['sqi'] = convert_int(item['SQI'])
        theStruct['nirs_upper'] = None
        theStruct['nirs_lower'] = None

        #print(theStruct)
        postRes = redcap.post_redcap(theStruct)
        print(postRes)

