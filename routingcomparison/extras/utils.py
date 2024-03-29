'''
    Extra function utility
    for cross app usage
'''

import requests as rq
import networkx as nx
import os
import logging

'''
    Env management

'''
def set_cwd_to_location(filepath):
    '''
        Used to set current working dir 
        of file to desier path     
    '''
    filepath = os.path.abspath(filepath)
    os.chdir(os.path.dirname(filepath))

def mkdir(path):
    '''
        For making 
    '''
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Folder: {path} created")

'''
    Mac converter

'''
def int_to_mac(num):
    '''
        Convert int to mac number (example format: 00:00..:00:00)
    '''
    mac = ':'.join(format((num >> i) & 0xFF, '02x') for i in (40, 32, 24, 16, 8, 0))
    return mac

def mac_to_int(mac):
    '''
        Convert hex mac to int
    '''
    return int(mac.translate(str.maketrans('','',":.- ")), 16)

def hostid_to_mac(host_id):
    '''
        Host index id to mac (ex: 1 to mac 00:00..00:01)
    '''
    mac_hex = "{:012x}".format(host_id)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str

def find_key_from_value(dic, value):
    for key, val in dic.items():
        if val == value:
            return key
    return None

'''
    Topology stat
'''
def get_topo():
    topo_json = rq.get('http://0.0.0.0:8080/topology_graph').json()
    return topo_json, nx.json_graph.node_link_graph(topo_json)

def get_host(max_display_mac=-1):
    # I have to some dirty hack to remove invalid hosts
    hosts = rq.get('http://0.0.0.0:8080/hosts').json()
    if max_display_mac > 0: 
        hosts = {'hosts': [host for host in hosts['hosts'] if mac_to_int(host['mac']) < 100]}
    return hosts

def get_link_to_port(ryu_rest_port=8080):
    # fix this to remote port
    link_to_port = rq.get(f'http://0.0.0.0:{ryu_rest_port}/link_to_port').json()
    # convert string key to int key
    link_to_port =  {int(key): {int(key2): value2 for key2, value2 in value.items()} for key, value in link_to_port.items()}
    return link_to_port

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
    topo_json, graph = get_topo()
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

# !Note Deprecate soon 
# 
def get_link_quality():
    '''
        Get from data from /link_quality
        currently working as a workaround 
        for link utilization
    '''

    link_quality_controller = rq.get('http://0.0.0.0:8080/link_quality').json()
    link_quality_mininet = rq.get('http://0.0.0.0:8000/link_quality').json()
    link_ping_stat = rq.get('http://0.0.0.0:8000/link_ping_stat').json()
    
    lqc_hmap = {}
    lqm_hmap = {}
    lps_hmap = {}
    
    for d in link_quality_controller:
        key = (d['src.dpid'], d['dst.dpid'])
        lqc_hmap[key] = d

    for d in link_quality_mininet:
        key = (d['src.dpid'], d['dst.dpid'])
        lqm_hmap[key] = d
    
    for d in link_ping_stat:
        key = (d['src.host'], d['dst.host'])
        lps_hmap[key] = d

    link_quality = []
    for key, lqc_value in lqc_hmap.items():
        lqm_value = lqm_hmap.get(key)
        lps_value = lps_hmap.get(key)
        if lqm_value == None: continue  
        link_quality.append({
            'src.dpid': key[0],
            'dst.dpid': key[1],
            'packet_loss': lps_value.get('packet_loss', None),
            'delay': lps_value.get('delay', None),
            'bandwidth': lqm_value.get('bandwidth', 1),
            'link_usage': lqc_value.get('link_usage', 0),
            'link_utilization': lqc_value.get('link_usage', 0) / lqm_value.get('bandwidth', 1) * 100,
        })
        
    return link_quality

# Will be replacement for get_link_quality
def get_link_info(mn_rest_addr: str = "0.0.0.0:8000"):
    '''
        Get from data from /link_quality
        currently working as a workaround 
        for link utilization
    '''

    link_quality_controller = rq.get(f'http://{mn_rest_addr}/link_quality').json()
    link_quality_mininet = rq.get(f'http://{mn_rest_addr}/link_info').json()
    link_ping_stat = rq.get(f'http://{mn_rest_addr}/link_ping_stat').json()
    
    lqc_hmap = {}
    lqm_hmap = {}
    lps_hmap = {}
    
    for d in link_quality_controller:
        key = (d['src.dpid'], d['dst.dpid'])
        lqc_hmap[key] = d

    for d in link_quality_mininet:
        key = (d['src.dpid'], d['dst.dpid'])
        lqm_hmap[key] = d
    
    for d in link_ping_stat:
        key = (d['src.host'], d['dst.host'])
        lps_hmap[key] = d

    link_quality = []
    for key, lqc_value in lqc_hmap.items():
        lqm_value = lqm_hmap.get(key)
        lps_value = lps_hmap.get(key)
        if lqm_value == None: continue  
        link_quality.append({
            'src.dpid': key[0],
            'dst.dpid': key[1],
            'packet_loss': lps_value.get('packet_loss', None),
            'delay': lps_value.get('delay', None),
            'bandwidth': lqm_value.get('bandwidth', 1),
            'link_usage': lqc_value.get('link_usage', 0),
            'link_utilization': lqc_value.get('link_usage', 0) / lqm_value.get('bandwidth', 1) * 100,
        })
        
    return link_quality