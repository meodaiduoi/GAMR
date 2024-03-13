import requests as rq
import networkx as nx
from networkx.readwrite import json_graph

from routingapp.common.routing_utils import *

from routingapp.common.datatype import NetworkGraph, LaunchOpt

# async def launchopt() -> LaunchOpt:
#     return LaunchOpt(APP_API_PORT,
#                      RYU_PORT)

# async def network_graph():
#     MAPPING, GRAPH = get_full_topo_graph()
#     if MULTI_DOMAIN == True:
#         GRAPH = json_graph.node_link_graph(
#             rq.get('http://0.0.0.0:8000/graph').json()
#         )
#     return NetworkGraph(MAPPING, GRAPH)