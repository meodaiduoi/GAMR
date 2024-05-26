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

def dict_str_to_int_key(str_key_dict: dict):
    '''
        convert
    '''
    int_key_dict = {}
    for key, value in str_key_dict.items():
        int_key_dict[int(key)] = value
    return int_key_dict
    
'''
    Topology stat
'''
def get_topo() -> nx.digraph:
    '''
        Return topo from json format back to nx.Digraoh object
    '''
    topo_json = rq.get('http://0.0.0.0:8080/topology_graph').json()
    return nx.json_graph.node_link_graph(topo_json)

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

def get_link_info_legacy():
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

def get_link_info(mn_rest_ip: str = "0.0.0.0:8000"):
    '''
        Get from data from /link_quality
        currently working as a workaround 
        for link utilization
    '''

    link_quality_controller = rq.get(f'http://{mn_rest_ip}/link_quality').json()
    # Link info but actually link to port but with extra info
    link_info_mininet = rq.get(f'http://{mn_rest_ip}/link_info').json()
    link_ping_stat = rq.get(f'http://{mn_rest_ip}/link_ping_stat').json()
    
    lqc_hmap = {}
    lim_hmap = {}
    lps_hmap = {}
    
    for d in link_quality_controller:
        key = (d['src.dpid'], d['dst.dpid'])
        lqc_hmap[key] = d

    for d in link_info_mininet:
        key = (d['src.dpid'], d['dst.dpid'])
        lim_hmap[key] = d
    
    for d in link_ping_stat:
        key = (d['src.host'], d['dst.host'])
        lps_hmap[key] = d

    link_quality = []
    for key, lqc_value in lqc_hmap.items():
        lim_value = lim_hmap.get(key)
        lps_value = lps_hmap.get(key)
        if lim_value == None: continue  
        link_quality.append({
            'src.dpid': key[0],
            'dst.dpid': key[1],
            'packet_loss': lps_value.get('packet_loss', None),
            'delay': lps_value.get('delay', None),
            'bandwidth': lim_value.get('bandwidth', 1),
            'link_usage': lqc_value.get('link_usage', 0),
            'link_utilization': lqc_value.get('link_usage', 0) / lim_value.get('bandwidth', 1) * 100,
        })
        
    return link_quality

# !NOTE:Multi-domain code reogernize later

def get_link_traffic_multi_controller():
    num_ctrler = rq.get(f'http://0.0.0.0:{8000}/controller_list').json()
    lqcs = []
    for i in range(len(num_ctrler)):
            lqcs += rq.get(f'http://0.0.0.0:{8080}/link_quality').json()
    return lqcs

from routingapp.common.network_stat_utils import (
    get_inter_group_edges, get_all_delta_port_stat, link_with_port_mn_to_hmap
)

def get_inter_group_edges_link_traffic():
    '''
        Only get bandwidth and link usage of
    '''
    
    json_graph = rq.get('http://0.0.0.0:8000/graph').json()
    graph = nx.json_graph.node_link_graph(json_graph)
    
    inter_group_edges = get_inter_group_edges(graph)
    deltal_port_stat = get_all_delta_port_stat()
    link_with_port = link_with_port_mn_to_hmap()
    
    inter_port_stat = []
    for ige in inter_group_edges:
        node1 = ige[0]
        port1 = link_with_port[(f's{ige[0]}', f's{ige[1]}')]['port1']
        node2 = ige[1]
        port2 = link_with_port[(f's{ige[0]}', f's{ige[1]}')]['port2']

        node1_port_stat = deltal_port_stat.get((node1, port1))
        node2_port_stat = deltal_port_stat.get((node2, port2))
        
        # ref:
        '''
            bandwidth = min(src_free_bandwidth, dst_free_bandwidth)
            link_usage = min(src_link_usage, dst_link_usage)
            
            link usage = delta upload+download min(src_dpid_port, dst_dpid_port)
            min()
        '''
        node1_traffic = node1_port_stat['tx_bytes'] + node1_port_stat['rx_bytes']
        node2_traffic = node2_port_stat['tx_bytes'] + node2_port_stat['rx_bytes']
        link_traffic = (min(node1_traffic, node2_traffic)) / (8*1000000)
        inter_port_stat.append({
            'src.dpid': node1,
            'dst.dpid': node2,
            'link_usage': link_traffic,
        })
    return inter_port_stat

def get_multi_domain_link_info():
# Only get link_usage
    link_traffic_multi_controller = get_link_traffic_multi_controller()
    link_traffic_inter_domain = get_inter_group_edges_link_traffic()
    link_traffic_all_net = link_traffic_inter_domain + link_traffic_multi_controller
        
    # get packetloss+delay directly from mininet
    link_ping_stat = rq.get('http://0.0.0.0:8000/link_ping_stat').json()

    ltan_hmap = {}
    lps_hmap = {}

    for d in link_traffic_all_net:
        key = (d['src.dpid'], d['dst.dpid'])
        ltan_hmap[key] = d

    for d in link_ping_stat:
        key = (d['src.host'], d['dst.host'])
        lps_hmap[key] = d

    lwp_hmap = link_with_port_mn_to_hmap()

    link_quality = []
    for key, lps_value in lps_hmap.items():
        ltan_value = ltan_hmap.get(key)
        lwp_value = lwp_hmap.get((f's{key[0]}',  f's{key[1]}'))
        print(lwp_value)
        # if lps_value == None: continue  
        link_quality.append({
            'src.dpid': key[0],
            'dst.dpid': key[1],
            'packet_loss': lps_value.get('packet_loss', None),
            'delay': lps_value.get('delay', None),
            'bandwidth': lwp_value.get('bw', 1),
            'link_usage': ltan_value.get('link_usage', 0),
            'link_utilization': ltan_value.get('link_usage', 0) / lwp_value.get('bandwidth', 1) * 100,
        })
