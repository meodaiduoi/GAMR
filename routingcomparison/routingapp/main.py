from routingapp.common.routing_utils import *
from routingapp.common.models import *
from routingapp.dependencies import *
import asyncio

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from networkx.readwrite import json_graph
import requests as rq

import time
import logging

# argParser = argparse.ArgumentParser()
# argParser.add_argument("rest_port", type=int, help="dynamicsdn startup rest api port")
# argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port or start port if multi_domain==True")
# argParser.add_argument("-md", "--multi_domain", type=bool, default=False, help="if network has more than 1 controller")
# args = argParser.parse_args()

# APP_API_PORT = args.rest_port
# RYU_PORT = args.ryu_port
# MULTI_DOMAIN= args.multi_domain

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title='Routing Api Network',
    description='Routing Api for networking application',
    summary="..."
)

setting: config.Setting = get_app_setting()

while True:
    try:
        MAPPING, GRAPH = get_full_topo_graph()
        if setting.MULTI_DOMAIN == True:
            GRAPH = json_graph.node_link_graph(
                rq.get('http://0.0.0.0:8000/graph').json()
            )
        break
    except (rq.ConnectionError, rq.ConnectTimeout):
        logging.error('Wait for server connecting...')
        time.sleep(5)
        continue

async def add_flow_adj():
    while True:
        try:
            if setting.MULTI_DOMAIN == False:
                adj_no_dup: dict = rq.get('http://0.0.0.0:8000/adj_list/True').json()
                debug_host_mapping = rq.get('http://0.0.0.0:8000/debug_switch_mapping').json()
                switchname_mapping =  rq.get('http://0.0.0.0:8000/switch_dpid').json()
            if setting.MULTI_DOMAIN == True:
                host_mn = rq.get('http://0.0.0.0:8000/host').json()
                sw_ctrler_mapping = rq.get('http://0.0.0.0:8000/sw_ctrler_mapping').json()
                link_info = get_link_info()

            solutions = {'route': []}
            for node1, adj_nodes in adj_no_dup.items():
                for node2 in adj_nodes:
                    logging.info(f'add debug flow from {switchname_mapping[node1]} to {switchname_mapping[node2]}')
                    solution = {
                            'src_host':debug_host_mapping[node1],
                            'dst_host':debug_host_mapping[node2],
                            'path_dpid':[switchname_mapping[node1],
                                        switchname_mapping[node2]]
                    }
                    solutions['route'].append(solution)
            print(setting.MULTI_DOMAIN, type(setting.MULTI_DOMAIN))
            if setting.MULTI_DOMAIN == False:
                send_flowrule(
                    create_flowrule_json(solutions, get_host(), get_link_to_port()))
            if setting.MULTI_DOMAIN == True:
                send_flowrule_multidomain_localhost(
                    create_flowrule_multidomain_json(solutions,
                                                    host_mn,
                                                    link_info),
                                                    sw_ctrler_mapping, 
                                                    setting.RYU_PORT)
            logging.info('Debug flow added sucessfully')
            # !NOTE: on next version add new adj flow on topology change
            await asyncio.sleep(500)
        except (rq.ConnectionError, rq.ConnectTimeout) as e:
            logging.error(f"Connection error retrying...")
            await asyncio.sleep(5)
        except TypeError as e:
            print(e)
            logging.error(f'Controller not ready retrying...')
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create async background task for adding adj flow
    asyncio.create_task(add_flow_adj())
    yield
    

app = FastAPI(lifespan=lifespan)

from routingapp.routers.pathfinder import simplerouting, ga
from routingapp.routers.legacy import simplerouting_legacy, ga_legacy
from routingapp.routers import debugdata

# Debug api
app.include_router(debugdata.router, prefix='/debug', tags=['debug'])

# Legacy api (only support single domain)
if setting.MULTI_DOMAIN is False:
    app.include_router(simplerouting_legacy.router, prefix="/legacy/simplerouting", tags=["Legacy"]) 
    app.include_router(ga_legacy.router, prefix="/legacy/ga", tags=["Legacy"]) 

# New multidomain api
app.include_router(simplerouting.router, prefix="/simplerouting", tags=["Simple routing"])
app.include_router(ga.router, prefix='/ga', tags=["Genetic Alogrithm"])

# test api
@app.get('/')
async def hello():
    return setting

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=setting.ROUTING_APP_PORT)