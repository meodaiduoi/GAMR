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
import requests as rq

from scenario.common.traffic_gen_utils import PingTraffic, HttpFileTransferController

if __name__ == '__main__':
    # Get list of host
    
    test_rule = [{
        'src_host': 1,
        'dst_host': 3
    }]

    rq.post('http://0.0.0.0:8001/single/rl/sec',
            data=json.dumps(test_rule)).json()
    
    PingTraffic().ping_single('h1', 'h2')
    
    