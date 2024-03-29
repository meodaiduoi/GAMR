import requests as rq
import networkx as nx
import json
import logging
from routingapp.common.routing_utils import *
from routingapp.common.datatype import NetworkStat

def get_topo():
    topo_json = rq.get('http://0.0.0.0:8080/topology_graph').json()
    return topo_json, nx.json_graph.node_link_graph(topo_json)

def get_host(max_display_mac=-1):
    # I have to some dirty hack to remove invalid hosts
    hosts = rq.get('http://0.0.0.0:8080/hosts').json()
    if max_display_mac > 0: 
        hosts = {'hosts': [host for host in hosts['hosts'] if mac_to_int(host['mac']) < 100]}
    return hosts

# !NOTE: Resolve this?
def link_info_mn_to_hmap():
    '''
        Convert link info from mn func
        "links_info()" into hashmap
    '''
    
    links_info = rq.get('http://0.0.0.0:8000/link_info').json()
    li_map = {}
    for d in links_info:
        key = (d['node1'], d['node2'])
        key2 = (d['node2'], d['node1'])
        li_map[key] = d
        li_map[key2] = d.copy()
        li_map[key2]['node1'], li_map[key2]['node2'] = li_map[key2]['node2'], li_map[key2]['node1']
        li_map[key2]['port1'], li_map[key2]['port2'] = li_map[key2]['port2'], li_map[key2]['port1']
    return li_map


def get_network_stat() -> NetworkStat:
    _, graph = get_topo()
    host_json = get_host()
    link_info = get_link_info()
    return NetworkStat(graph, host_json, link_info)

def get_network_stat_legacy() -> NetworkStat:
    _, graph = get_topo()
    host_json = get_host()
    link_info = get_link_info_legacy()
    return NetworkStat(graph, host_json, link_info)

def network_stat_serve():
    ...