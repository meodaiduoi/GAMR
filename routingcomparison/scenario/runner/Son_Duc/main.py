# Duc tao ra json nay (Xem ) # Tham so chuyen vao la so request + so host cua graph
# {
#   "route": [
#     {
#       "src_host": 1,
#       "dst_host": 3
#     },
#     {
#       "src_host": 6,
#       "dst_host": 7
#     },
#     {
#       "src_host": 7,
#       "dst_host": 9
#     }
#   ]
# }

# Duc: dua them 1 file bao gom cac host duoc ping
# {
#   "hostname_list": [
#     "h1", "h3", "h6", "h7", "h9"
#   ],
#   "timeout": "0.3" # Tham so chuyen vao
# }

# {'hostname_list': ['h19', 'h13', 'h10', 'h5', 'h17', 'h6', 'h15', 'h11', 'h14', 'h9', 'h16', 'h18', 'h2', 'h3', 'h12'], 'timeout': 0.3}

import random
import requests
import time
import json

def create_route_list(number_hosts, number_request):
    routes = [] 
    pings = []
    
    for i in range(number_request):
        src_host = random.randint(1, number_hosts)
        dst_host = random.randint(1, number_hosts)
        while src_host == dst_host:
            dst_host = random.randint(1, number_hosts)
            
        route = {
            "src_host": src_host,
            "dst_host": dst_host
            }
        routes.append(route)
        cmd = (
            f"""curl -X 'POST' 'http://0.0.0.0:8001/upload_speed/' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{{"ip": "10.0.0.{dst_host}", "port": 8001, "size": 50}}'"""
        )
        pings.append(
            {
                "hostname": "h" + str(src_host),
                "cmd": cmd,
                "wait": True
            }
        )
    return routes, pings
        
def init_host_list(hosts):
    initHosts_list = []
    
    for i_host in hosts:
        # hosts.add("h"+str(route["src_host"]))
        # hosts.add("h"+str(route["dst_host"]))
        initHosts_list.append({
            "hostname": "h"+str(i_host),
            "cmd": '''
                    ../../venv11/bin/python3.11 \
                    mn_app/simplehttpserver/http_file_transfer.py 0.0.0.0 8001
                    ''',
            "wait": False
        })
    return initHosts_list

def pingHTTP(ping):
    print(ping)
    print(requests.post('http://0.0.0.0:8000/run_popen', data=json.dumps(ping)).json())

url_addflow_GA = "http://0.0.0.0:8001/routing/ga"
url_addflow_minhop = "http://0.0.0.0:8001/routing/min_hop"
url_cmd_host = "http://0.0.0.0:8000/run_xterm"
url_addflow_dijsktra = "http://0.0.0.0:8001/routing/dijkstra"
url_ping = "http://0.0.0.0:8000/ping"

fix_number_hosts, fix_number_request = 20, 25
fix_list = [i for i in range(1, fix_number_hosts + 1)]
fix_list_hosts = fix_list[:int(fix_number_hosts/2)]
fix_list_servers = fix_list[int(fix_number_hosts/2):]

initHosts_list = init_host_list(fix_list_hosts)
for i in range(len(initHosts_list)):
  res = requests.post('http://0.0.0.0:8000/run_xterm', data=json.dumps(initHosts_list[i]))
  if res.status_code == 200:
        print("Open h" + str(i))

def make_api_call():
    routes, pings = create_route_list(fix_number_hosts, fix_number_request)
    data = {
        "route": routes
    }
    # add flow
    res = requests.post(url_addflow_minhop, json=data)
    
    if res.status_code == 200:
        print("Add flow ok")
        
    time.sleep(3)
    # ping http server
    for ping in pings:
        pingHTTP(ping)
    
    time.sleep(20)
#     return is_break

start_time = time.time()

while time.time() - start_time < 1800:
    make_api_call()
    time.sleep(3)
    
# routes = create_route_list(19, 10)
# print(routes)
# pings = create_host_list(routes, 0.3)
# print(pings)
# post len api: http://0.0.0.0:8001/routing

# post len api: http://0.0.0.0:8000/ping
