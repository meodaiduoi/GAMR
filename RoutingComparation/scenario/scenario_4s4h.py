import requests as rq

import tomllib
try:
    with open("config.toml", "rb") as f:
        toml_dict = tomllib.load(f)
except tomllib.TOMLDecodeError:
    print("Yep, definitely not valid.")

RESTHOOKMN_PORT = toml_dict['service-port']['resthookmn']
DYNAMICSDN_PORT = toml_dict['service-port']['dynamicsdn']
SIMPLEHTTPSERVER_PORT = toml_dict['service-port']['simplehttpserver']

def run_simplehttpserver(hostlist: list[str]):
    result = {}
    for host in hostlist:
        data = {
          "hostname": host,
          "cmd": '',
          "wait": True
        }
        result[host] = rq.post(f'http://0.0.0.0:{RESTHOOKMN_PORT}/run_cmd', 
                               json=data).json()['result'].decode('latin-1')
    return result

def heartbeat_simplehttpserver(hostlist: list[str]):
    result = {}
    for host in hostlist:
        data = {
          "hostname": host,
          "cmd": '''curl -o /dev/null -s -w "%{http_code}\n" 'http://0.0.0.0:8002/''',
          "wait": True
        }
        result[host] = rq.post('http://0.0.0.0:{RESTHOOKMN_PORT}/run_popen', 
                               json=data).json()['result'].decode('latin-1')
    return result

if __name__ == '__main__':
    devicename = rq.get('http://0.0.0.0:8000/device_name').json()
    hostname = devicename['hostname']
    switchname = devicename['switchname']
    
    run_simplehttpserver(hostname)
    

