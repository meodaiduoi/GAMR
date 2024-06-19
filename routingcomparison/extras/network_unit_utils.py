import requests as rq
import networkx as nx
import json
import os
import logging
from extras.datatype import NetworkStat
from extras.sys_util import mac_to_int, dict_str_to_int_key

# Load ENV variable if fail fallback to default value
try:
    RYU_PORT = int(os.getenv('RYU_PORT'))
    OFP_PORT = int(os.getenv('PFP_PORT'))
except TypeError:
    RYU_PORT = 8080
    OFP_PORT = 6633

'''
    Topology / Graph / Host / Switch
    Get from api
'''
def get_topo():
    try:
        topo_json = rq.get('http://0.0.0.0:8080/topology_graph').json()
    except (ConnectionError, TimeoutError):
        logging.error("Can't connect to remote controller API to get topo graph")
        return None, None
    return topo_json, nx.json_graph.node_link_graph(topo_json)

def get_host(max_display_mac=-1):
    # I have to some dirty hack to remove invalid hosts
    hosts = rq.get('http://0.0.0.0:8080/hosts').json()
    if max_display_mac > 0: 
        hosts = {'hosts': [host for host in hosts['hosts'] if mac_to_int(host['mac']) < 100]}
    return hosts

def get_endpoint_info(host_mac, host_json):
    '''
        Get dpid and port_no of host connected to switch \n
        assume that host only connect to 1 switch
    '''
    for host in host_json['hosts']:
        if host['mac'] == host_mac:
            return mac_to_int(host['port']['dpid']), mac_to_int(host['port']['port_no'])

def get_full_topo_graph(max_display_mac=100) -> tuple[dict, nx.DiGraph]:
    '''
        get network topology with hostId and switchId \n 
        mapping of ryu restapi
    '''
    # dict, nx.DiGraph    
    graph = get_topo()
    host_json = get_host(max_display_mac)

    # Add host to graph
    for host in host_json['hosts']:
        dpid_int = mac_to_int(host['port']['dpid'])
        host_int = mac_to_int(host['mac'])
        # print(f'dpid_int: {dpid_int}, host_int: {host_int}')
        
        # Add node to graph
        graph.add_node(f'h{host_int}', type='host')
        # add bi-directional link between host and switch
        graph.add_edge(f'h{host_int}', dpid_int, type='host')
        graph.add_edge(dpid_int, f'h{host_int}', type='host')

    # Mapping host h{int} to int
    mapping: dict = dict(zip(graph.nodes(), range(1, len(graph.nodes())+1)))

    return mapping, graph
'''
    Port related function
'''
def get_link_to_port(ryu_rest_port=8080):
    # fix this to remote port
    link_to_port = rq.get(f'http://0.0.0.0:{ryu_rest_port}/link_to_port').json()
    # convert string key to int key
    link_to_port =  {int(key): {int(key2): value2 for key2, value2 in value.items()} for key, value in link_to_port.items()}
    return link_to_port

def link_with_port_mn_to_hmap():
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

def get_sw_ctrler_mapping():
    '''
    Process sw_ctrler_mapping json from mininet
    into usable int key dict with 
    key is switch and value is controller it belong to
    {switch: ctrler}
    Ex: {2: 0, 5: 0, 6: 0, 1: 1, 3: 1, 4: 1}
    '''
    sw_ctrler_mapping_json = rq.get('http://0.0.0.0:8000/sw_ctrler_mapping').json()
    return dict_str_to_int_key(sw_ctrler_mapping_json)

def get_inter_group_edges(graph: nx.DiGraph):
    '''
        Input: Graph
        Return: inter group edge (adj node)
        bettween 2 parttion by checking attribute 'controller'
        of each node which controller group it belong to
    '''
    group_membership = nx.get_node_attributes(graph, 'controller')
    inter_group_edges = []
    for u, v, data in graph.edges(data=True):
        # I don't like using try catch in this part
        # just to check if group_membership has key
        # hope in the future i can find a better
        # implemtation than this...
        try:
            if group_membership[u] != group_membership[v]:
                # inter_group_edges.append((u, v, data))
                inter_group_edges.append((u, v))
        except KeyError:
            pass
    return inter_group_edges

def get_controller_list():
  """Fetches controller list from the API and converts string/int keys to int keys.

  Returns:
    A list of dictionaries with integer keys.
  """
  ctrler_list = rq.get('http://0.0.0.0:8000/controller_list').json()

  # Use list comprehension for concise conversion
  new_ctrler_list = [{int(key): value} for ctrler in ctrler_list for key, value in ctrler.items() if key.isdigit()]

  return new_ctrler_list

def get_all_delta_port_stat():
    ''' Get delta port stat of all controllers in the network
    Return:
        hashmap of (dpid, port): {delta_port_stat}
    '''
    deltal_port_stat = []
    ctrler_list = get_controller_list()
    
    for ctrler in ctrler_list:
        for key, value in ctrler.items():
            deltal_port_stat += rq.get(f'http://{value.get("ip")}:{RYU_PORT+key}/delta_port_stat').json()

    dps_hmap = {}
    for d in deltal_port_stat:
        key = (d['dpid'], d['port_no'])
        dps_hmap[key] = d