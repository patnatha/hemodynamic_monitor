import serial
import serial.tools.list_ports
import sys
import glob
import struct
from datetime import datetime

BAUDRATE = 9600
HEMOSPHERE = "hemosp"
VIGILENCE = "vigII"
NIRS = "nirs"

def check_device_stream(COM):
    ser = serial.Serial(COM, baudrate=BAUDRATE, timeout=1)
    try:
        #Read two full lines
        theVal = ser.readline()
        theVal += ser.readline()
        ser.close()

        #Decode the values
        decVal = theVal.decode("cp1252")
        
        #Count number of commas
        commaCnt = len(decVal.split(","))
        if(commaCnt == 6 or commaCnt == 12):
            print("FOUND NIRS:", COM)
            return(NIRS)

        ser.close()
    except Exception as err:
        print("YASE")
        print(err)
        ser.close()
   
def connected_devices():
    connDevices = {NIRS: None, HEMOSPHERE: None, VIGILENCE: None}
    try:
        a = serial.tools.list_ports.comports()
        for p in a:
            theDevice = p.device
            theFind = None
            
            #print(p.name, p.pid, p.vid, p.manufacturer, p.product, p.serial_number)
            if(not p.product == None and p.product.startswith("USB-Serial")):
                theFind = check_device_stream(theDevice)

            if(theFind != None):
                connDevices[theFind] = theDevice

        return(connDevices)
    except Exception as err:
        print("HMM")
        print(err)
        return connDevices

def connect_swan():
    try:
        conDev = connected_devices()
        if(conDev[HEMOSPHERE] != None):
            return(serial.Serial(conDev[HEMOSPHERE], baudrate=BAUDRATE, timeout=3))
        elif(conDev[VIGILENCE] != None):
            return(serial.Serial(conDev[VIGILENCE], baudrate=BAUDRATE, timeout=3))
        else:
            return(None)
    except Exception as err:
        print(err)
        return None

def parse_swan(dataPack, prefix):
    splitIt = dataPack.split(prefix)
    if(len(splitIt) == 2):
        theVal = ""
        for i in range(0, len(splitIt[1])):
            theChar = splitIt[1][i]
            if(theChar.isdigit() or theChar == "."):
                theVal += theChar
            else:
                break
            if(len(theVal) > 6):
                return(None)

        return(float(theVal))
    else:
        return(None)

def read_swan(ser):
    try:
        theLine = b''
        foundStartByte = False
        emptyReads = 0
        while True:
            theChar = ser.read(1)
            if(len(theChar) == 0): 
                emptyReads == 0
            if(emptyReads > 10):
                break

            if(foundStartByte and theChar == b'\x03'):
                break
            elif(foundStartByte):
                theLine += theChar
            elif(theChar == b'\x02'):
                foundStartByte = True

        decodedLine = theLine.decode("cp1252")
        prefixes = {"B": "temp", 
            "C": "CO", 
            "T": "CO_STAT",
            "J": "EDV",
            "E": "RVEF",
            "S": "SV",
            "V": "SVO2",
            "Q": "SQI"}
        results = dict()
        results["datetime"] = datetime.now()
        for itemUnpack in prefixes.keys():
            results[prefixes[itemUnpack]] = parse_swan(decodedLine, itemUnpack) 
        return(results)
    except Exception as err:
        print(err)
        return(None)

def connect_nirs():
    try:
        conDev = connected_devices()
        if(conDev[NIRS] != None):
            return(serial.Serial(conDev[NIRS], baudrate=BAUDRATE, timeout=3))
        else:
            return(None)
    except Exception as err: 
        print(err)
        return None

def read_nirs(ser):
    try:
        #Read a line and parse it up
        theLine = ser.readline()
        decodedLine = theLine.decode("cp1252")
        splitLine = decodedLine.split(",")
        
        #Check quality of read line
        if(len(splitLine) == 6):
            #Parse the nirs upper
            nirsUpper = int(splitLine[0])
            if(nirsUpper == -1): nirsUpper = None
            
            #parse the nirs lower
            nirsLower = int(splitLine[1])
            if(nirsLower == -1): nirsLower = None

            #Build return structures
            nirs_res = {"nirs_upper": nirsUpper, "nirs_lower": nirsLower}
            return(nirs_res)
        else:
            return(None)

    except Exception as err:
        print("read_nirs")
        print(err)
        return(None)
