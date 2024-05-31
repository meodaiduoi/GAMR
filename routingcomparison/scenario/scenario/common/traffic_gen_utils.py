import requests as rq
import json
def get_host_ls():
    # host_ls
    return rq.get('http://0.0.0.0:8000/host').json()

class PingTraffic:
    def __init__(self, mn_hook_api_ip: str | None = '0.0.0.0',
                 mn_hook_api_port: int | None = 8000) -> None:
        self.mn_api_ip = mn_hook_api_ip
        self.mn_api_port = mn_hook_api_port

    def ping_single(self, src_host: str, dst_host: str,
                    timeout:int | None = 3, count:int | None = 3):
        request = {
            "src_hostname": src_host,
            "dst_hostname": dst_host,
            "timeout": f'{timeout}',
            "count": f'{count}'
        }
        return rq.post(f'http://{self.mn_api_ip}:{self.mn_api_port}/ping_single', json.dumps(request)).json()
        
    
    def ping_multi(self, host_ls: str, timeout: int | None = 3):
        '''
           Ping between all host in list
           ex input: ['h1', 'h2', 'h3',...] 
        '''
        request = {
            "hostname_list": host_ls,
            "timeout": f'{timeout}'
        }
        return rq.post(f'http://{self.mn_api_ip}:{self.mn_api_port}/ping', json.dumps(request)).json()
    
    def ping_all(self, timeout: int | None = 3):
        return rq.post(f'http://{self.mn_api_ip}:{self.mn_api_port}/pingall', json.dumps({'timeout': f'{t}'})).json()

class HttpFileTransferController:
    def __init__(self, host_ls: dict, 
                 mn_api_ip: str | None = '0.0.0.0',
                 mn_api_port: int| None = 8000,
                 app_port: int | None = 8001):
        self.mn_api_ip = mn_api_ip
        self.mn_api_port = mn_api_port
        self.app_port = app_port
        self.host_ls = host_ls
        
        for hostname, _ in host_ls.items():
            if self.is_online(hostname) is True:
                continue
            
            req = {
                "hostname": f"{hostname}",
                "cmd": f" ../../venv11/bin/python3.11 \
                        mn_app/simplehttpserver/http_file_transfer.py 0.0.0.0 {self.app_port} \
                        ",
                "wait": False
            }
            rq.post(f'http://{self.mn_api_port}:{self.mn_api_port}/run_popen', 
                    data=json.dumps(req)).json()

    @property
    def is_online(self, hostname):
        req = {
            "hostname": f"{hostname}",
            "cmd": f"curl -X 'GET' 'http://0.0.0.0:{self.app_port}'",
            "wait": True
        }
        result = rq.post(f'http://{self.mn_api_port}:{self.mn_api_port}/run_popen', 
                         data=json.dumps(req)).json()
        return json.loads(result['result'])['status']
    
    def file_upload(self, src_hostname: str, dst_hostname, size: int | None = 10):
        req = ({
            "hostname": f"{src_hostname}",
            "cmd":f"""curl -X 'POST' 'http://0.0.0.0:{self.app_port}/upload_speed/' \
                 -H 'accept: application/json' -H \
                 'Content-Type: application/json' -d \
                 '{{"ip": "{self.host_ls[dst_hostname]["ip"]}", \
                 "port": {self.app_port}, "size": 50}}'""",
            "wait": True
        })
        result = rq.post(f'http://{self.mn_api_port}:{self.mn_api_port}/run_popen', 
                    data=json.dumps(req)).json()
        return json.loads(result['result'])['status']
    
    def file_download(self, src_hostname: str, dst_hostname, size: int | None = 10):
        req = ({
            "hostname": f"{src_hostname}",
            "cmd":f"""curl -X 'POST' 'http://0.0.0.0:{self.app_port}/download_speed/' \
                 -H 'accept: application/json' -H \
                 'Content-Type: application/json' -d \
                 '{{"ip": "{self.host_ls[dst_hostname]["ip"]}", \
                 "port": {self.app_port}, "size": 50}}'""",
            "wait": True
        })
        result = rq.post(f'http://{self.mn_api_port}:{self.mn_api_port}/run_popen', 
                         data=json.dumps(req)).json()
        return json.loads(result['result'])['status']
    
    def respone_time(self, src_hostname, dst_hostname):
        req = ({
            "hostname": f"{src_hostname}",
            "cmd":f"""curl -X 'POST' 'http://0.0.0.0:{self.app_port}/download_speed/' \
                 -H 'accept: application/json' -H \
                 'Content-Type: application/json' -d \
                 '{{"ip": "{self.host_ls[dst_hostname]["ip"]}", \
                 "port": {self.app_port}}}'""",
            "wait": True
        })
        result = rq.post(f'http://{self.mn_api_port}:{self.mn_api_port}/run_popen', 
                         data=json.dumps(req)).json()
        return json.loads(result['result'])['status']