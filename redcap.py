import requests

tokenFile = "~/Documents/hemodynamic_monitor/token.auth"
postUrl = "https://redcap.wakehealth.edu/redcap/api/"

def post_recprd(theDatas):
    data = {
      'token': 'C65A9C1E66A98E3F35BF8EF99DDAB4B0',
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

    data['data'] = json.dumps([{
        'record_id': 0,
        'name': 'test',
        'datetime': '2021-10-23 03:44:30',
        'temperature': 36.9,
        'cardiac_output': '4.0',
        'cardiac_output_stat': 4.2,
        'end_diastolic_volume': 300,
        'rv_ejection_fraction': 35,
        'stroke_volume': 45,
        'svo2': 95,
        'sqi': 3,
        'nirs_upper': 85,
        'nirs_lower': 80
        }])
    r = requests.post('https://redcap.wakehealth.edu/redcap/api/',data=data)
    print(r.json())
    
    return(r.status_code)
  