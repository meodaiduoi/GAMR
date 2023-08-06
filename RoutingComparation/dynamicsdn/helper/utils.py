import requests as rq
import networkx as nx
import json

def get_link_to_port():
    # fix this to remote port
    link_to_port = rq.get('http://0.0.0.0:8080/link_to_port').json()
    # convert string key to int key
    link_to_port =  {int(key): {int(key2): value2 for key2, value2 in value.items()} for key, value in link_to_port.items()}
    return link_to_port

def hostid_to_mac(host_id):
    mac_hex = "{:012x}".format(host_id)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str

def get_endpoint_info(host_mac, host_json):
    '''
        Get dpid and port_no of host connected to switch
        assume that host only connect to 1 switch
    '''
    for host in host_json['hosts']:
        if host['mac'] == host_mac:
            return int(host['port']['dpid']), int(host['port']['port_no'])
        
def flowrule_template(dpid, in_port, out_port, hostmac_src, hostmac_dst):
    return {
        "dpid": dpid,
        "cookie": 1,
        "cookie_mask": 1,
        "table_id": 0,
        "idle_timeout": 3000,
        "hard_timeout": 3000,
        "priority": 2,
        "flags": 1,
        "match": {
            "in_port": in_port,
            "dl_dst": hostmac_src,
            "dl_src": hostmac_dst,
            "actions":[{
                "type":"OUTPUT","port": out_port,
            }]
        }
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

def create_flowrule_json(solution, host_json, link_to_port):
    solution = solution['path'][0]
    path_dpid = solution['path_dpid']
    print(path_dpid)
    hostmac_src = hostid_to_mac(solution['src_host'])
    hostmac_dst = hostid_to_mac(solution['dst_host'])

    _, src_endpoint_port = get_endpoint_info(hostmac_src, host_json)
    _, dst_endpoint_port = get_endpoint_info(hostmac_dst, host_json)

    dpid_flowport = {}
    for i in range(len(path_dpid)-1):
        # find in_port and out_port of first switch
        if i == 0:
            in_port = src_endpoint_port
            print(path_dpid[i], path_dpid[i+1])
            out_port = link_to_port[path_dpid[i]][path_dpid[i+1]][0]
            dpid_flowport[path_dpid[i]] = (in_port, out_port)
            continue
        # find in_port and out_port of switch inbetween
        print(path_dpid[i], path_dpid[i+1])
        in_port = link_to_port[path_dpid[i-1]][path_dpid[i]][1]
        out_port = link_to_port[path_dpid[i]][path_dpid[i+1]][0]
        dpid_flowport[path_dpid[i]] = (in_port, out_port)

    # find in_port and out_port of last switch
    in_port = link_to_port[path_dpid[-1]][path_dpid[-2]][0]
    out_port = dst_endpoint_port
    dpid_flowport[path_dpid[-1]] = (in_port, out_port)

    # create bi-directional flowrule
    flowrules = []
    for dpid, flowport in dpid_flowport.items():
        flowrules.append(flowrule_template(dpid, flowport[0], flowport[1], hostmac_src, hostmac_dst))
        flowrules.append(flowrule_template(dpid, flowport[1], flowport[0], hostmac_dst, hostmac_src))
    return flowrules

def send_flowrule(flowrules):
    for flowrule in flowrules:
        rq.post('http://0.0.0.0:8080/flowrules', json=json.dumps(flowrules))