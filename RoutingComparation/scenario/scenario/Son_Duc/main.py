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

def create_route_list(number_hosts, number_request):
    routes = [] 
    
    for i in range(number_request):
        src_host = random.randint(i, number_hosts)
        dst_host = random.randint(1, number_hosts)
        while src_host == dst_host:
            dst_host = random.randint(1, number_hosts)
            
        route = {
            "src_host": src_host,
            "dst_host": dst_host
            }
        routes.append(route)
        
    return routes
        
def create_host_list(routes, timeout):
    hosts = set()
    
    for route in routes:
        hosts.add("h"+str(route["src_host"]))
        hosts.add("h"+str(route["dst_host"]))
    
    host_list = list(hosts)
    
    result = {
        "hostname_list": host_list,
        "timeout": timeout
    }
    
    return result

url_addflow = "http://0.0.0.0:8001/routing"
url_ping = "http://0.0.0.0:8000/ping"

def make_api_call():
    routes = create_route_list(20, 10)
    is_break = False
    data = {
        "route": routes
    }
    
    res = requests.post(url_addflow, json=data)
    
    if res.status_code == 200:
        print("Add flow ok")
        
    time.sleep(3)
        
    pings = create_host_list(routes, "0.3")
    res_ping = requests.post(url_ping, json=pings)
    if res_ping.status_code == 200:
        print("Ping ok")
        is_break = True
    
    time.sleep(20)
    return is_break

start_time = time.time()

while time.time() - start_time < 3600:
    is_break = make_api_call()
    time.sleep(3)
    
# routes = create_route_list(19, 10)
# print(routes)
# pings = create_host_list(routes, 0.3)
# print(pings)
# post len api: http://0.0.0.0:8001/routing

# post len api: http://0.0.0.0:8000/ping
