from datetime import datetime

def returnName(theDatetime):
    theName = theDatetime.strftime("%Y-%m-%d")
    theName += "_1" #this is the OR for this logger
    return(theName)

