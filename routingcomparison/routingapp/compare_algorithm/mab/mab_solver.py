import networkx as nx
from extras.utils import *
from routingapp.common.routing_utils import *
from routingapp.common.models import MultiRouteTasks

def ga_solver(tasks: MultiRouteTasks):
    '''
        Routing using GA alogrithm
    '''
    
    _, graph = get_topo()
    host_json = get_host()
    link_info = get_link_info()

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
