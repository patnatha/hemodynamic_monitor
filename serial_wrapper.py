import serial
import sys
import glob
import struct
from datetime import datetime

BAUDRATE = 9600
HEMOSPHERE = "hemosp"
VIGILENCE = "vigII"
NIRS = "nirs"

def avail_ports():
    if sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    return ports

def parse_device_type(byteArr):
    decData = byteArr.decode("cp1252")
    if(decData.startswith("N2515-8265-41")):
        return(HEMOSPHERE)
    elif(decData.startswith("N2515-8110-32")):
        return(VIGILENCE)
    else:
        parsedData = decData.split(",")
        if(len(parsedData) == 6):
            try:
                for item in parsedData:
                    if(int(item) < -1 or int(item) > 100):
                        return(None)
                return(NIRS)
            except Exception as err:
                print(err)
                return(none)
        else:
            return(None)

def device_type(COM):
    try:
        ser = serial.Serial(COM, baudrate=BAUDRATE, timeout=1) 
        try:
            theLine = b''
            foundStartByte = False
            emptyReads = 0
            while True:
                theChar = ser.read(1)
                
                if(len(theChar) == 0):
                    emptyReads += 1
                
                if(foundStartByte and theChar == b'\x03'):
                    break
                elif(foundStartByte):
                    theLine += theChar
                elif(theChar == b'\x02'):
                    foundStartByte = True
                

                if(emptyReads > 10): 
                    break
            ser.close()

            return(parse_device_type(theLine))
        except Exception as err:
            print(err)
            ser.close()
            return None
    except Exception as err:
        print(err)
        return None

def connect_swan():
    try:
        ap = avail_ports()
        for p in ap:
            dt = device_type(p)
            if(dt == HEMOSPHERE or dt == VIGILENCE):
                return(serial.Serial(p, baudrate=BAUDRATE, timeout=3))
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
        ap = avail_ports()
        for p in ap:
            dt = device_type(p) 
            if(dt == NIRS):
                return(serial.Serial(p, baudrate=BAUDRATE, timeout=3))
    except Exception as err: 
        print(err)
        return None


