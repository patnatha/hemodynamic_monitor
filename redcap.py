import requests
import json

tokenFile = "/home/pi/Documents/hemodynamic_monitor/token.auth"
postUrl = "https://redcap.wakehealth.edu/redcap/api/"

def get_token():
    f = open(tokenFile)
    theToken = f.read().strip("\n")
    f.close()
    return(theToken)
loaded_token = get_token()

def convert_int(theVal):
    if(theVal == None):
        return(None)
    else:
        try:
            return(str(int(round(theVal, 0))))
        except:
            return(None)

def convert_one_decimal(theVal):
    if(theVal == None):
        return(None)
    else:
        try:
            return(str(round(theVal,1)))
        except:
            return(None)

def post_redcap(theDatas):
    data = {
      'token': loaded_token,
      'content': 'record',
      'action': 'import',
      'format': 'json',
      'type': 'flat',
      'overwriteBehavior': 'normal',
      'forceAutoNumber': 'true',
      'data': '',
      'returnContent': 'count',
      'returnFormat': 'json'
    }

    #Build the final data strcut
    theSendStruct = {'record_id': 0}
    for key in theDatas:
        theSendStruct[key] = theDatas[key]

    #Convert the final data struct to JSON
    data['data'] = json.dumps([theSendStruct])

    #Send the final data struct
    #print(data)
    r = requests.post('https://redcap.wakehealth.edu/redcap/api/',data=data)
   
    #Parse the resulting output
    if(r.status_code != 200):
        print(r.json())
        return(-2)
    elif(r.status_code == 200 and r.json()['count'] != 1):
        print(r.json())
        return(-1)
    else:
        return(1)
 
