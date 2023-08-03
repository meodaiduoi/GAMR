import requests as rq

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
