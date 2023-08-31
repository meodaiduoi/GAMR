import sqlite3
import logging
import requests as rq
import argparse
import time
import os
import datetime

from extras.utils import *

argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")

def set_cwd_to_file_location():
    file_path = os.path.abspath(__file__)
    os.chdir(os.path.dirname(file_path))
set_cwd_to_file_location()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.info(f'current working dir: {os.getcwd()}')

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Folder: {path} created")

folder = 'db'
mkdir(folder)
current_time = datetime.datetime.now()
formatted_time = current_time.strftime("%H-%M-%S--%d-%m-%Y")
con = sqlite3.connect(f'{folder}/linkcost-{formatted_time}.db')

# Create table with 
try:
    con.execute('''CREATE TABLE linkcost (
                time_id INTEGER, 
                src_dpid INTEGER,
                dst_dpid INTEGER,
                delay REAL,
                packet_loss REAL,
                link_usage REAL,
                link_utilization REAL   
            )''')
    con.commit()
    logging.info("Table created successfully")
except sqlite3.OperationalError:
    logging.info("Table already exists")

timeID_initial = 0
start_time = time.time()

while time.time() - start_time < 3650:
    try:
        data = get_link_quality()
        for item in data:
            timeid = timeID_initial
            src = item.get('src.dpid')
            dst = item.get('dst.dpid')
            delay = item.get('delay')
            packet_loss = item.get('packet_loss')
            link_usage = item.get('link_usage')
            link_utilization = item.get('link_utilization')
            
            con.execute('''
                        INSERT INTO linkcost (time_id, src_dpid, dst_dpid, delay, packet_loss, link_usage, link_utilization)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (timeid, src, dst, delay, packet_loss, link_usage, link_utilization))
        con.commit()
        timeID_initial += 1
        time.sleep(3)
    
    except rq.ConnectionError or rq.ConnectTimeout:
        logging.error("Connection err..., reconnecting")
        time.sleep(3)

    except KeyboardInterrupt:
        con.close()
        logging.info("Keyboard interrupt exiting...")
        break      