import requests
import json
import sqlite3
import time
import threading
import signal

tokenFile = "/home/pi/Documents/hemodynamic_monitor/token.auth"
postUrl = "https://redcap.wakehealth.edu/redcap/api/"
dbFile = "backup.db"
tableName = "to_log"

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

def create_sqlite_table():
    conn = sqlite3.connect(dbFile)
    cur = conn.cursor()
    sql = "CREATE TABLE IF NOT EXISTS " + tableName + " (record_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, the_text TEXT);"
    cur.execute(sql)
    conn.commit()
    conn.close()
    
def log_later(theDatas):
    create_sqlite_table()

    conn = sqlite3.connect(dbFile)
    cur = conn.cursor()

    sql = 'INSERT INTO ' + tableName + ' (the_text) VALUES("' + json.dumps(theDatas).replace('"', '\'') + '");'
    cur.execute(sql)

    conn.commit()
    conn.close()

def survail_db_to_upload():
    create_sqlite_table()

    while True:
        try:
            conn = sqlite3.connect(dbFile)
            cur = conn.cursor()

            sql = "SELECT record_id, the_text FROM " + tableName
            toDel = []
            for row in cur.execute(sql):
                theDatas = json.loads(row[1].replace("'","\""))
                #print(theDatas)
                postRes = post_redcap(theDatas)
                if(postRes == 1):
                    toDel.append(str(row[0]))
            conn.commit()
            conn.close()

            print("SQLITE Posted:", len(toDel))
            conn = sqlite3.connect(dbFile)
            cur = conn.cursor()
            for itemDel in toDel:
                sql = "DELETE FROM " + tableName + " WHERE record_id = " + itemDel
                cur.execute(sql)
            conn.commit()
            conn.close()

        except Exception as err:
            print("survail_db_to_upload ERROR:", err)
        time.sleep(60)

survailThread = threading.Thread(target=survail_db_to_upload, args=())
survailThread.daemon = False
survailThread.start()

def post_redcap(theDatas):
    try:
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
        #log_later(theDatas)
        #return
        r = requests.post('https://redcap.wakehealth.edu/redcap/api/',data=data)
       
        #Parse the resulting output
        if(r.status_code != 200):
            print(r.json())
            log_later(theDatas)
            return(-2)
        elif(r.status_code == 200 and r.json()['count'] != 1):
            print(r.json())
            log_later(theDatas)
            return(-1)
        else:
            return(1)
    except Exception as err:
        print("post_redcap ERROR:", err)
        log_later(theDatas)

