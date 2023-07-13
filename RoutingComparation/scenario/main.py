import requests as rq

# TODO: add config file here later

def run_simplehttpserver(hostlist: list[str]):
    result = {}
    for host in hostlist:
        data = {
          "hostname": host,
          "cmd": '''curl -o /dev/null -s -w "%{http_code}\n" 'http://0.0.0.0:8002/''',
          "wait": True
        }
        result[host] = rq.post('http://0.0.0.0:8001/run_cmd', json=data).json()['result'].decode('latin-1')
    return result

def heartbeat_simplehttpserver(hostlist: list[str]):
    result = {}
    for host in hostlist:
        data = {
          "hostname": host,
          "cmd": '''curl -o /dev/null -s -w "%{http_code}\n" 'http://0.0.0.0:8002/''',
          "wait": True
        }
        result[host] = rq.post('0.0.0.0:8081/run_popen', json=data).json()['result'].decode('latin-1')
    return result

if __name__ == '__main__':
    devicename = rq.get('http://0.0.0.0:8000/device_name').json()
    hostname = devicename['hostname']
    switchname = devicename['switchname']
    
    run_simplehttpserver(hostname)
    

