import requests as rq

def get_link_to_port():
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
        "priority": 1,
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