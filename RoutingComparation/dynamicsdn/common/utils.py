import requests as rq
import networkx as nx
import json
import logging
from common.utils import *
from extras.utils import *

def flowrule_template(dpid, in_port, out_port, hostmac_src, hostmac_dst, priority=1):
    return {
        "dpid": dpid,
        "cookie": 1,
        "cookie_mask": 1,
        "table_id": 0,
        "idle_timeout": 3000,
        "hard_timeout": 3000,
        "priority": priority,
        "flags": 1,
        "match": {
            "in_port": in_port,
            "dl_src": hostmac_src,
            "dl_dst": hostmac_dst,
        },
        "actions": [{
            "type": "OUTPUT",
            "port": out_port,
        }]
    }
    
def get_topo():
    topo_json = rq.get('http://0.0.0.0:8080/topology_graph').json()
    return topo_json, nx.json_graph.node_link_graph(topo_json)

def get_host(max_display_mac=-1):
    # I have to some dirty hack to remove invalid hosts
    hosts = rq.get('http://0.0.0.0:8080/hosts').json()
    if max_display_mac > 0: 
        hosts = {'hosts': [host for host in hosts['hosts'] if mac_to_int(host['mac']) < 100]}
    return hosts

def get_key(dict, value):
    for key, val in dict.items():
        if val == value:
           return key

def get_link_info(link_info_url):
    links_info = rq.get(link_info_url).json()
    li_map = {}
    for d in links_info:
        key = (d['node1'], d['node2'])
        key2 = (d['node2'], d['node1'])
        li_map[key] = d
        li_map[key2] = d.copy()
        li_map[key2]['node1'], li_map[key2]['node2'] = li_map[key2]['node2'], li_map[key2]['node1']
        li_map[key2]['port1'], li_map[key2]['port2'] = li_map[key2]['port2'], li_map[key2]['port1']
    return li_map
    
def result_to_json(result, mapping):
    result_list = []
    # print(result.chromosome)
    # print(mapping)
    for request in result.chromosome:
        print("Request", request)
        src = get_key(mapping,request[0])
        dst = get_key(mapping,request[1])
        src = int(src[1:])
        dst = int(dst[1:])
        request_result_map = []
        for i in request[2][1:-1]:
            request_result_map.append(int(get_key(mapping, i)))
        # print("Hello")
        route = {
            'src_host': src,
            'dst_host': dst,
            'path_dpid': request_result_map
        }
        result_list.append(route)
    result_json = {
        'route': result_list
    }
    print(result_list)
    return result_json  

def create_flowrule_json(solutions, host_json, link_to_port, important=False):
    flowrules = []
    for solution in solutions['route']:
        path_dpid = [int(dpid) for dpid in solution['path_dpid']]
        hostmac_src = hostid_to_mac(solution['src_host'])
        hostmac_dst = hostid_to_mac(solution['dst_host'])

        if (hostmac_src or hostmac_dst) == None or hostmac_src == hostmac_dst:
            raise (ValueError("invaild host mac"))
        
        logging.debug('endpoint info' , hostmac_src, hostmac_dst)
        _, src_endpoint_port = get_endpoint_info(hostmac_src, host_json)
        _, dst_endpoint_port = get_endpoint_info(hostmac_dst, host_json)
        
        dpid_flowport = {
            'eth_src': hostmac_src,
            'eth_dst': hostmac_dst,
            'dpid_path': [],
            'port_pair_path': []
        }
        
        for i in range(len(path_dpid)-1):
            # start
            if i == 0:
                in_port = src_endpoint_port
                out_port = link_to_port[path_dpid[i]][path_dpid[i+1]][0]
                # print(f'start {i}')
                # print(in_port, out_port)
                dpid_flowport['dpid_path'].append(path_dpid[i])
                dpid_flowport['port_pair_path'].append([in_port, out_port])
                            
            # inbetween
            if i > 0 and i <= len(path_dpid)-2:
                # print(f'inbetween: {i}')
                # ra o dau nay thi vao o dau kia
                in_port = link_to_port[path_dpid[i-1]][path_dpid[i]][1]        
                out_port = link_to_port[path_dpid[i]][path_dpid[i+1]][0]
                dpid_flowport['dpid_path'].append(path_dpid[i])
                dpid_flowport['port_pair_path'].append([in_port, out_port])
                # print(in_port, out_port)

            # finish
            if i >= len(path_dpid)-2:
                # print(f'finish {i+1}')
                in_port = link_to_port[path_dpid[i]][path_dpid[i+1]][1]
                out_port = dst_endpoint_port
                # +1 for -2
                dpid_flowport['dpid_path'].append(path_dpid[i+1])
                dpid_flowport['port_pair_path'].append([in_port, out_port])
                # print(in_port, out_port)

        # create bi-directional flowrule
        for dpid, port_pair in zip(dpid_flowport['dpid_path'], dpid_flowport['port_pair_path']):
            flowrules.append(flowrule_template(dpid, port_pair[0], port_pair[1], hostmac_src, hostmac_dst))
            flowrules.append(flowrule_template(dpid, port_pair[1], port_pair[0], hostmac_dst, hostmac_src))

    return flowrules

def send_flowrule(flowrules, ryu_ip='0.0.0.0', ryu_rest_port=8080):
    status = []
    for flowrule in flowrules:
        result = rq.post(f'http://{ryu_ip}:{ryu_rest_port}/stats/flowentry/add', data=json.dumps(flowrule))
        status.append({
            'status': result.status_code,
            'flowrule': flowrule
        })
    print(status)
    return status
"""
{'dpid': 2,
   'cookie': 1,
   'cookie_mask': 1,
   'table_id': 0,
   'idle_timeout': 3000,
   'hard_timeout': 3000,
   'priority': 1,
   'flags': 1,
   'match': {'in_port': 1,
    'dl_src': '00:00:00:00:00:02',
    'dl_dst': '00:00:00:00:00:09'},
   'actions': [{'type': 'OUTPUT', 'port': 5}]}
"""

def create_flowrule_multidomain_json(solutions, host_json_mn,
                                     links_info, important=False):
    flowrules = []
    
    for solution in solutions['route']:
        path_dpid = [int(dpid) for dpid in solution['path_dpid']]
        hostmac_src = host_json_mn[f'h{solution["src_host"]}']['mac']
        hostmac_dst = host_json_mn[f'h{solution["dst_host"]}']['mac']
        print('endpoint info' , hostmac_src, hostmac_dst)
        
        if (hostmac_src or hostmac_dst) == None or hostmac_src == hostmac_dst:
            raise (ValueError("invaild host mac"))
        
        src_endpoint_port = links_info[(f'h{solution["src_host"]}',
                                        f's{path_dpid[0]}')]['port2']
        dst_endpoint_port = links_info[(f's{path_dpid[-1]}',
                                        f'h{solution["dst_host"]}')]['port1']
        
        dpid_flowport = {
            'eth_src': hostmac_src,
            'eth_dst': hostmac_dst,
            'dpid_path': [],
            'port_pair_path': []
        }
        
        for i in range(len(path_dpid)-1):
            # start
            if i == 0:
                in_port = src_endpoint_port
                out_port = links_info[(f's{path_dpid[i]}',
                                      f's{path_dpid[i+1]}')]['port1']
                # print(f'start {i}')
                # print(in_port, out_port)
                dpid_flowport['dpid_path'].append(path_dpid[i])
                dpid_flowport['port_pair_path'].append([in_port, out_port])
                            
            # inbetween
            if i > 0 and i <= len(path_dpid)-2:
                # print(f'inbetween: {i}')
                # ra o dau nay thi vao o dau kia
                in_port = links_info[(f's{path_dpid[i-1]}',
                                      f's{path_dpid[i]}')]['port2']        
                out_port = links_info[(f's{path_dpid[i]}', 
                                       f's{path_dpid[i+1]}')]['port1']
                dpid_flowport['dpid_path'].append(path_dpid[i])
                dpid_flowport['port_pair_path'].append([in_port, out_port])
                # print(in_port, out_port)
            
            # finish
            if i >= len(path_dpid)-2:
                # print(f'finish {i+1}')
                in_port = links_info[(f's{path_dpid[i]}',
                                      f's{path_dpid[i+1]}')]['port2']
                out_port = dst_endpoint_port
                # +1 for -2
                dpid_flowport['dpid_path'].append(path_dpid[i+1])
                dpid_flowport['port_pair_path'].append([in_port, out_port])
                # print(in_port, out_port)

        # create bi-directional flowrule
        for dpid, port_pair in zip(dpid_flowport['dpid_path'], dpid_flowport['port_pair_path']):
            flowrules.append(flowrule_template(dpid, port_pair[0], port_pair[1], hostmac_src, hostmac_dst))
            flowrules.append(flowrule_template(dpid, port_pair[1], port_pair[0], hostmac_dst, hostmac_src))

    return flowrules

def send_flowrule_multidomain_localhost(flowrules, sw_ctrler_mapping, ryu_rest_port):
    status = []
    for flowrule in flowrules:
        result = rq.post(
            # When request sw_ctrler_mapping from mn api, key(aka switch)
            # are number in str type so flowrule['dpid'] need to be converted
            # into str to access key value dict
            f'http://0.0.0.0:{ryu_rest_port+sw_ctrler_mapping[str(flowrule["dpid"])]}/stats/flowentry/add', 
            data=json.dumps(flowrule))
        
        status.append({
            'status': result.status_code,
            'flowrule': flowrule
        })
    print(status)
    return status    

def send_flowrule_multidomain_remote(flowrule):
    ...
    
    