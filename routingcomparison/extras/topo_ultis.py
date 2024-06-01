import requests as rq
import networkx as nx
from extras.network_helper_utils

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