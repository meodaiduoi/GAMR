import requests as rq
import networkx as nx
import json
import logging

def get_link_to_port(ryu_rest_port=8080):
    # fix this to remote port
    link_to_port = rq.get(f'http://0.0.0.0:{ryu_rest_port}/link_to_port').json()
    # convert string key to int key
    link_to_port =  {int(key): {int(key2): value2 for key2, value2 in value.items()} for key, value in link_to_port.items()}
    return link_to_port

def hostid_to_mac(host_id):
    mac_hex = "{:012x}".format(host_id)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str

def mac_to_int(mac):
    return int(mac.translate(str.maketrans('','',":.- ")), 16)

def get_endpoint_info(host_mac, host_json):
    '''
        Get dpid and port_no of host connected to switch
        assume that host only connect to 1 switch
    '''
    for host in host_json['hosts']:
        if host['mac'] == host_mac:
            return mac_to_int(host['port']['dpid']), mac_to_int(host['port']['port_no'])
        
def flowrule_template(dpid, in_port, out_port, hostmac_src, hostmac_dst, priority=2):
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

def get_host():
    return rq.get('http://0.0.0.0:8080/hosts').json()

def get_key(dict, value):
    for key, val in dict.items():
        if val == value:
           return key
        
def result_to_json(result, mapping):
    resul_list = []
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
        path = {
            'src_host': src,
            'dst_host': dst,
            'path_dpid': request_result_map

        }
        resul_list.append(path)
    result_json = {
        "path": resul_list
    }
    print(resul_list)
    return result_json  

def create_flowrule_json(solutions, host_json, link_to_port):
    for solution in solutions['path']:
        path_dpid = solution['path_dpid']
        hostmac_src = hostid_to_mac(solution['src_host'])
        hostmac_dst = hostid_to_mac(solution['dst_host'])

        if (hostmac_src or hostmac_dst) == None or hostmac_src == hostmac_dst:
            raise (ValueError("invaild host mac"))
        
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
    flowrules = []
    for dpid, port_pair in zip(dpid_flowport['dpid_path'], dpid_flowport['port_pair_path']):
        flowrules.append(flowrule_template(dpid, port_pair[0], port_pair[1], hostmac_src, hostmac_dst))
        flowrules.append(flowrule_template(dpid, port_pair[1], port_pair[0], hostmac_dst, hostmac_src))

    return flowrules

def send_flowrule(flowrules, ryu_rest_port):
    status = []
    for flowrule in flowrules:
        result = rq.post(f'http://0.0.0.0:{ryu_rest_port}/stats/flowentry/add', data=json.dumps(flowrule))
        status.append({
            'status': result.status_code,
            'src_host': flowrule.get('src_host'),
            'dst_host': flowrule.get('dst_host'),
            'dpid_path': flowrule.get('dpid_path')
        })
    return status
            
def get_full_topo_graph():
    # dict, nx.DiGraph    
    topo_json, graph = get_topo()
    host_json = get_host()

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

    # print graph to json
    # print(nx.node_link_data(graph))
    
    # Mapping host h{int} to int
    mapping: dict = dict(zip(graph.nodes(), range(1, len(graph.nodes())+1)))

    return mapping, graph