def int_to_mac(num):
    mac = ':'.join(format((num >> i) & 0xFF, '02x') for i in (40, 32, 24, 16, 8, 0))
    return mac

def link_exist(net, node1, node2):
    try:
        net.linkInfo('h1', 's3')
        return True
    except KeyError:
        return False
    
def enable_stp(net):
    for switch in net.switches:
        switch.cmd(f'ovs-vsctl set bridge {switch.name} stp_enable=true')