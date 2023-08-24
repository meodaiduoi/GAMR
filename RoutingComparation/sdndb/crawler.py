import sqlite3
import logging
import requests as rq
import argparse
import time
import os

argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")

con = sqlite3.connect('db/linkcost.db')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def set_cwd_to_file_location():
    file_path = os.path.abspath(__file__)
    os.chdir(os.path.dirname(file_path))
set_cwd_to_file_location()
print(os.getcwd())

# Create table with 
try:
    con.execute('''CREATE TABLE linkcost
            (
            time_id INTEGER, 
            src_dpid INTEGER,
            dst_dpid INTEGER,
            delay REAL,
            packet_loss REAL,
            link_usage REAL,
            free_bandwidth REAL   
                
                )''')
    con.commit()
    logging.info("Table created successfully")
except sqlite3.OperationalError:
    logging.info("Table already exists")

timeID_initial = 0
while True:
    try:
        data = rq.get('http://0.0.0.0:8080/link_quality').json()
        for item in data:
            timeid = timeID_initial
            src = item.get('src.dpid')
            dst = item.get('dst.dpid')
            delay = item.get('delay')
            packet_loss = item.get('packet_loss')
            link_usage = item.get('link_usage')
            free_bandwidth = item.get('free_bandwidth')
            
            con.execute('''
                        INSERT INTO linkcost (time_id, src_dpid, dst_dpid, delay, packet_loss, link_usage, free_bandwidth)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (timeid, src, dst, delay, packet_loss, link_usage, free_bandwidth))
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
        