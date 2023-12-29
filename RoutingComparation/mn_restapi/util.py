import time
import logging
import networkx as nx
import re

import mininet
from mininet.net import Mininet, Host, Node, Link
from extras.utils import mac_to_int, int_to_mac

def command_sanitization(cmd: str, open_in_term=False):
    '''
        sanitization for remote json request \n
        external_scr: \n
            True if open in external terminal (ex: xterm, gnome-terminal)
            False for direct execution
    '''
    # remove json format
    cmd = re.sub(r'\n|\\|\s\s\**', '', cmd)
    # convert char " ' " and " " " into \' and \"
    if open_in_term == True:
        cmd = cmd.replace(r'"', r'\"')
    return cmd

def topo_to_nx(net: Mininet,
                    include_host=True,
                    sw_name_is_dpid=False) -> nx.Graph:
    '''
        converting Mininet network to networkx graph
    '''
    graph = nx.DiGraph()
    for link in net.links:
        # Add edges to the graph
        src = link.intf1.node.name
        dst = link.intf2.node.name

        if sw_name_is_dpid:
            try:
                src = int(net.get(src).dpid)
            except: AttributeError
                
            try:
                dst = int(net.get(dst).dpid)
            except: AttributeError
        
        graph.add_edge(src, dst)
        graph.add_edge(dst, src)

    if include_host == False:
        host_names = [host.name for host in net.hosts]
        # remove hosts from graph
        for host_name in host_names:
            graph.remove_node(host_name)
    return graph

def sw_to_ctrler_mapping_converter(sw_parted_ls):
    """
        Convert parted list from part_graph()
        from 2d list into switch to controller mapping
        used for pushing flow rule the right controller
        (domain)
        
        ex: [[1,2,3][4,5,6,7]...]
        key(switch): value(controller)
        to -> {1: 0, 2: 0, 3:0, 4:1, 5:1, ...}
    """
    mapping = {}
    for idx, sw_parted in enumerate(sw_parted_ls):
        mapping[idx] = sw_parted
    
    inverted_dict = {}
    for key, value_list in mapping.items():
        for value in value_list:
            inverted_dict[value] = key
    return inverted_dict
    

def adj_dict(graph: nx.Graph) -> dict:
    '''
        For getting adj switch list
        Return ex: 
        {'s1': ['s2'], 's2': ['s1', 's3'], 
        's3': ['s2', 's4'], 's4': ['s3']}
    '''
    adj_list = {}
    for node in graph.nodes:
        adj_list[node] = list(graph.neighbors(node))
    return adj_list

def adj_ls_no_dup_route(adj_dict: dict) -> dict:
    '''
        Remove duplicate route from adj list \n
        Return ex:
        {'s1': ['s2'], 's2': ['s3'], 's3': ['s4']}
    '''
    key_list = adj_dict.keys()
    edge_list_visted = []
    
    filter_dict = {}
    for node1, adj_node_ls in adj_dict.items():
        for node2 in adj_node_ls:
            if ((node2, node1) not in edge_list_visted) and \
                ((node1, node2) not in edge_list_visted):
                edge_list_visted.append((node1, node2))
                if node1 not in filter_dict.keys():
                    filter_dict[node1] = [node2]
                else:
                    filter_dict[node1].append(node2)
    return filter_dict

def get_hostnames_and_switchnames(net: Mininet):
    host_names = [host.name for host in net.hosts]
    switch_names = [switch.name for switch in net.switches]
    return host_names, switch_names

def enable_stp(net):
    '''

    '''
    for switch in net.switches:
        switch.cmd(f'ovs-vsctl set bridge {switch.name} stp_enable=true')

def stp_check_forward_state(net):
    '''
        Return if the forwarding state is enabled \n
        True if is FOWARDING, False if BLOCKING, DISCOVER, DISABLE.
    '''
    switch = net.switches[0]
    return switch.cmdPrint(f'ovs-ofctl show {switch.name} | grep -o FORWARD | head -n1') == "FORWARD\r\n"

def wait_for_stp(net):
    '''
        Wait for STP to be enabled
    '''
    while not stp_check_forward_state(net):
        time.sleep(1)
    logging.info("STP is in FOWARD state")
    
    
def host_popen_ping(net: Mininet,
                    node1, node2,
                    count=10, timeout=1,
                    interval=0.1,
                    return_hostname=False):
    '''
        Ping between 2 given host
    '''
    host1 = net.getNodeByName(node1)
    host2 = net.getNodeByName(node2)

    cmd = f'ping {host2.IP()} -c {count} -W {timeout}'
    if interval <= 0.01:
        cmd += ' -A'
    else:
        cmd += f' -i {interval}'
    result = host1.popen(
        cmd,
        shell=True).communicate()
    
    output = result[0].decode('latin-1')
    print(output)
    err = result[1].decode('latin-1')
    # Extract packet loss percentage
    try:
        packet_loss = re.search(r"([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[Ee]([+-]?\d+))?% packet loss", output).group(1)
        packet_loss = float(packet_loss) / 100
    except AttributeError:
        packet_loss = None
        logging.error("Error: Cannot find packet loss in ping output, Try to add flow")

    try: 
        avg_rtt = re.search(r"avg\/max\/mdev = (\d+\.\d+)", output).group(1)
        avg_rtt = float(avg_rtt)
    except AttributeError:
        # Extract average RTT
        avg_rtt = None
        # print("Average RTT:", avg_rtt, "ms")
        logging.error("Error: Cannot find avg/max/mdev in ping output, Try to add flow")
    
    print(err)

    if return_hostname == True:
        src_hostname = str(host1)
        dst_hostname = str(host2)

    if return_hostname == False:
        src_hostname = mac_to_int(host1.MAC())
        dst_hostname = mac_to_int(host2.MAC())
        
    return {
        'src_host': src_hostname,
        'dst_host': dst_hostname,
        'packet_loss': packet_loss,
        'delay': avg_rtt
    }  
    
