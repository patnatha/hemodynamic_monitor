import serial_wrapper
from serial_wrapper import NIRS, VIGILENCE, HEMOSPHERE, BAUDRATE
import redcap
from redcap import convert_int, convert_one_decimal
import which_or
import time
import threading
from datetime import datetime
import board
from digitalio import DigitalInOut, Direction, Pull

#This the list for collating centrally and is shared between threads
queueLock = threading.Lock()
queue = []

#This is the list of used ports shared between threads
conPorts = {}
conPortLock = threading.Lock()

#The log variable and associate mulithtreading lock
toLog = False
toLogLock = threading.Lock()

#The GPIO access to the nirs connected LED
def nirsLed(onOff):
    theLed = DigitalInOut(board.D27)
    theLed.direction = Direction.OUTPUT
    theLed.value = onOff
nirsLed(False)

#The GPIO access to the SWAN connected LED
def swanLed(onOff):
    theLed = DigitalInOut(board.D4)
    theLed.direction = Direction.OUTPUT
    theLed.value = onOff
swanLed(False)

#The function for monitoring the logging button
def monitorLogButton():
    logButton = DigitalInOut(board.D20)
    logButton.direction = Direction.INPUT
    logButton.pull = Pull.UP

    logLed = DigitalInOut(board.D17)
    logLed.direction = Direction.OUTPUT
    logLed.value = False

    global toLog

    while True:
        logLed.value = not logButton.value
        toLogLock.acquire()
        toLog = (not logButton.value)
        toLogLock.release()
        time.sleep(1)

def swanReading():
    swanSer = None
    global queue, queueLock, conPorts, conPortLock
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
                swanLed(True)
            else:
                #If not port available wait 5 seconds
                swanLed(False)
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
                swanLed(False)
                conPortLock.release()
            else:
                #Push this datapoint into the list buffer
                queueLock.acquire()
                queue.append(swanLine)
                queueLock.release()

def nirsReading():
    nirsSer = None
    global queue, queueLock, conPorts, conPortLock
    while True:
        if(nirsSer == None):
            #Get the port lock
            conPortLock.acquire()

            #Try and connect to NIRS
            nirsSer = serial_wrapper.connect_nirs(conPorts)
            
            #Set this port as used
            if(nirsSer != None):
                conPorts[NIRS] = nirsSer.port
                nirsLed(True)
            else:
                #If no port available wait 5 seconds
                nirsLed(False)
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
                nirsLed(False)
                conPortLock.release()
            else:
                #Push the datapoint into the list buffer
                queueLock.acquire()
                queue.append(nirsLine)
                queueLock.release()

#Start the swan thread
swanThread = threading.Thread(target=swanReading, args=(), daemon=True)
swanThread.start()

#start the nirs thread
nirsThread = threading.Thread(target=nirsReading, args=(), daemon=True)
nirsThread.start()

#start the logging button thread
loggingButton = threading.Thread(target=monitorLogButton, args=(), daemon=True)
loggingButton.start()

while True:
    #Sleep for two seconds 
    time.sleep(5)
   
    #List variable for snending
    toSend = []
    
    #Lock the queue
    queueLock.acquire()

    #ITerate through all items in the queue
    numOfElem = len(queue)
    curTime = datetime.now()
    for i in range(0,numOfElem):
        #Pop the first item in the queue
        item = queue.pop(0)

        if((curTime - item['datetime']).seconds > 5):
            #Process item if greater than 5 seconds in the past
            toSend.append(item)
        else:
            #Requeue the item if too recent
            queue.append(item)

    #Release the queue lock
    queueLock.release()

    #print(len(queue), len(toSend))
    #if(len(toSend) > 0):
    #    print("\t", toSend[0]['datetime'].strftime("%H:%M:%S"), toSend[-1]['datetime'].strftime("%H:%M:%S"))

    #Check to see if the log button has been pressed
    toLogLock.acquire()
    toLogIt = toLog
    toLogLock.release()

    #Process the item
    if(toLogIt):
        #Collate the list to combine to the nearest second
        timeStamps = {}
        for index, item in enumerate(toSend):
            theTs = item['datetime'].strftime("%Y-%m-%d %H:%M:%S")
            if(theTs not in timeStamps): timeStamps[theTs] = []
            timeStamps[theTs].append(index)

        #Iterate through the time stamps
        for ts in timeStamps:   
            #Get the first item for the timestamp
            item = toSend[timeStamps[ts][0]]

            #Build the translation struct to red cap
            theStruct = {}
            theStruct['name'] = which_or.returnName(item['datetime'])
            theStruct['datetime'] = ts
            theStruct['temperature'] = None
            theStruct['cardiac_output'] = None
            theStruct['cardiac_output_stat'] = None
            theStruct['svo2'] = None
            theStruct['sqi'] = None
            theStruct['nirs_upper'] = None
            theStruct['nirs_lower'] = None

            #Get the values for this timestamp
            for theInd in timeStamps[ts]:
                item = toSend[theInd]
                try:
                    theStruct['temperature'] = convert_one_decimal(item['temp'])
                    theStruct['cardiac_output'] = convert_one_decimal(item['CO'])
                    theStruct['cardiac_output_stat'] = convert_one_decimal(item['CO_STAT'])
                    theStruct['svo2'] = convert_int(item['SVO2'])
                    theStruct['sqi'] = convert_int(item['SQI'])
                except:
                    #print("Not Swan")
                    notSwan = True

                try:
                    theStruct['nirs_upper'] = convert_int(item['nirs_upper'])
                    theStruct['nirs_lower'] = convert_int(item['nirs_lower'])
                except: 
                    #print("Not NIRS")
                    notNirs = True

            #Check to make sure not an empty struct
            postIt = False
            for key in theStruct:
                if(key != "name" and key != "datetime" and theStruct[key] != None):
                    postIt = True
                    break

            if(postIt):
                #print(theStruct)
                postRes = redcap.post_redcap(theStruct)
                print("Posted:", postRes)

