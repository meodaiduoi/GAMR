import time
import logging

# ---- TODO Reoganize this section in future
def int_to_mac(num):
    mac = ':'.join(format((num >> i) & 0xFF, '02x') for i in (40, 32, 24, 16, 8, 0))
    return mac

def mac_to_int(mac):
    return int(mac.translate(str.maketrans('','',":.- ")), 16)

def hostid_to_mac(host_id):
    mac_hex = "{:012x}".format(host_id)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str
# ----

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