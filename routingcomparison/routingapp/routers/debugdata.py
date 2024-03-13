from routingapp.common.models import *
from routingapp.dependencies import *
from fastapi import APIRouter

router = APIRouter()

@router.get('/network_graph')
async def get_network_graph():
    '''
        Get network graph and nodes mapping as json
    '''
    return network_graph()
    
@router.get('/get_launch_opt')
async def get_launch_opt():
    '''
        Get launch options of main.py
    '''
    return launchopt()
