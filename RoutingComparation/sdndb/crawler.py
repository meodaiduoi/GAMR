import sqlite3
import logging
import requests as rq
import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")

con = sqlite3.connect('linkcost.db')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Create table with 
try:
    con.execute('''CREATE TABLE linkcost
            (src, dst, delay, packetloss, link_utilization)''')
except sqlite3.OperationalError:
    logging.info("Table already exists")


while True:
    try:
        # rq.get()
        ...
    except KeyboardInterrupt:
        logging.info("Exiting...")