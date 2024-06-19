import os
import logging 

'''
    Env management

'''
def set_cwd_to_location(filepath):
    '''
        Used to set current working dir 
        of file to desier path     
    '''
    filepath = os.path.abspath(filepath)
    os.chdir(os.path.dirname(filepath))

def mkdir(path):
    '''
        For making 
    '''
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Folder: {path} created")

'''
    Mac converter

'''
def int_to_mac(num):
    '''
        Convert int to mac number (example format: 00:00..:00:00)
    '''
    mac = ':'.join(format((num >> i) & 0xFF, '02x') for i in (40, 32, 24, 16, 8, 0))
    return mac

def mac_to_int(mac):
    '''
        Convert hex mac to int
    '''
    return int(mac.translate(str.maketrans('','',":.- ")), 16)

def hostid_to_mac(host_id: int):
    '''
        Host index id to mac (ex: 1 to mac 00:00..00:01)
    '''
    mac_hex = "{:012x}".format(host_id)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str

def find_key_from_value(dic, value):
    for key, val in dic.items():
        if val == value:
            return key
    return None

def dict_str_to_int_key(str_key_dict: dict):
    '''
        convert str int-key to int key
    '''
    int_key_dict = {}
    for key, value in str_key_dict.items():
        int_key_dict[int(key)] = value
    return int_key_dict




    