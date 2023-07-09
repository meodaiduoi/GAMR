# fastapi init project
# uvicorn main:app --reload
#
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from .helper.utils import *
from .helper.models import *

import requests as rq 

app = FastAPI()

origins = []

@app.get("/")
def hello_world():
    return {"Hello": "World"}




class Solution:
    ...



@app.post("/create_flowrule_json")
def create_flowrule_json(solution, host_json, link_to_port):
    solution = solution['path'][0]
    path_dpid = solution['path_dpid']

    hostmac_src = hostid_to_mac(solution['src_host'])
    hostmac_dst = hostid_to_mac(solution['dst_host'])

    src_endpoint_dpid, src_endpoint_port = get_endpoint_info(hostmac_src, host_json)
    dst_endpoint_dpid, dst_endpoint_port = get_endpoint_info(hostmac_dst, host_json)

    dpid_flowport = {}
    for i in range(len(path_dpid)-1):
        # find in_port and out_port of first switch
        if i == 0:
            in_port = src_endpoint_port
            out_port = link_to_port[path_dpid[i]][path_dpid[i+1]][0]
            dpid_flowport[path_dpid[i]] = (in_port, out_port)
            continue
        # find in_port and out_port of switch inbetween
        in_port = link_to_port[path_dpid[i-1]][path_dpid[i]][1]
        out_port = link_to_port[path_dpid[i]][path_dpid[i+1]][0]
        dpid_flowport[path_dpid[i]] = (in_port, out_port)

    # find in_port and out_port of last switch
    in_port = link_to_port[path_dpid[-1]][path_dpid[-2]][0]
    out_port = dst_endpoint_port
    dpid_flowport[path_dpid[-1]] = (in_port, out_port)

    # create bi-directional flowrule
    flowrules = []
    for dpid, flowport in dpid_flowport.items():
        flowrules.append(flowrule_template(dpid, flowport[0], flowport[1], hostmac_src, hostmac_dst))
        flowrules.append(flowrule_template(dpid, flowport[1], flowport[0], hostmac_dst, hostmac_src))
    return flowrules