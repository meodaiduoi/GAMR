from functools import lru_cache

from fastapi import Depends
import requests as rq
import networkx as nx
from networkx.readwrite import json_graph

from routingapp.common.routing_utils import *
from routingapp.common.datatype import NetworkGraph, LaunchOpt

from . import config

@lru_cache
def get_app_setting() -> config.Setting:
    return config.Setting()

async def network_graph(setting: config.Setting = Depends(get_app_setting)):
    MAPPING, GRAPH = get_full_topo_graph()
    if setting.MULTI_DOMAIN == True:
        GRAPH = json_graph.node_link_graph(
            rq.get('http://0.0.0.0:8000/graph').json()
        )
    return NetworkGraph(MAPPING, GRAPH)