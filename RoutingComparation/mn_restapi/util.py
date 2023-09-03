import time
import logging
import networkx as nx
import re

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

def convert_network(net):
    '''
        converting Mininet network to networkx graph
    '''
    graph = nx.DiGraph()
    for link in net.links:
         # Add edges to the graph
        src = link.intf1.node.name
        dst = link.intf2.node.name
        graph.add_edge(src, dst)
        graph.add_edge(dst, src)
    return graph

def link_exist(net, node1, node2):
    '''
        Check if Link between 2 given node exist or not
    '''
    try:
        net.linkInfo('h1', 's3')
        return True
    except KeyError:
        return False

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