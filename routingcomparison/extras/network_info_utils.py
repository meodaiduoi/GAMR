'''
    Extra function utility
    for cross app usage
'''

import requests as rq
import networkx as nx
from extras.datatype import NetworkStat
from extras.network_unit_utils import get_host,  get_full_topo_graph

'''
    Get link info such as
    packetloss, delay, link utilization and link usage from
    single / multi - domain 
'''

def get_link_info_single():
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

# Multi-domain link_traffic
from extras.network_unit_utils import (
    get_inter_group_edges, get_all_delta_port_stat, link_with_port_mn_to_hmap
)

# NOTE: make this dynamic work with config soon
def get_link_info_multi_controller():
    '''
        Get link quality from all api controller from mininet
    '''
    num_ctrler = rq.get(f'http://0.0.0.0:{8000}/controller_list').json()
    lqcs = []
    for i in range(len(num_ctrler)):
            lqcs += rq.get(f'http://0.0.0.0:{8080+i}/link_quality').json()
    return lqcs

def get_inter_group_edges_link_info():
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
    link_traffic_multi_controller = get_link_info_multi_controller()
    link_traffic_inter_domain = get_inter_group_edges_link_info()
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

'''
    Get network stat as dataclass
'''
# TODO: fix this func and add host node 'h{n}' to graph
# def get_network_stat() -> NetworkStat:
#     # _, graph = get_full_topo_graph()
#     graph = get_full_topo_graph()
#     host_json = get_host()
#     link_info = get_link_info()
#     return NetworkStat(graph, host_json, link_info)

def get_network_stat_single() -> NetworkStat:
    mapping, graph = get_full_topo_graph()
    host_json = get_host()
    link_info = get_link_info_single()
    return NetworkStat(graph, mapping, host_json, link_info)