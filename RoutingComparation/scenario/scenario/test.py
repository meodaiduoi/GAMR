cmd = """curl -X 'POST' 'http://0.0.0.0:8001/upload_speed/' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"ip": "10.0.0.2", "port": 8001, "size": 50}'"""
# cmd = """curl -X 'POST' '0.0.0.0:8001/upload_speed/' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"ip": "10.0.0.2", "port": 8001, "size": 100}"""

data  =  {
    "hostname": "h1",
    "cmd": cmd,
    "wait": True
}
print(data)

{'hostname': 'h3', 'cmd': 'curl -X \'POST\' \'http://0.0.0.0:8001/upload_speed/\' -H \'accept: application/json\' -H \'Content-Type: application/json\' -d \'{"ip": "10.0.0.2", "port": 8001, "size": 50}\'', 'wait': False}
{'hostname': 'h1', 'cmd': 'curl -X \'POST\' \'http://0.0.0.0:8001/upload_speed/\' -H \'accept: application/json\' -H \'Content-Type: application/json\' -d \'{"ip": "10.0.0.2", "port": 8001, "size": 50}\'', 'wait': True}