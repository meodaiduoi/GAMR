from routingapp.common.routing_utils import *
from routingapp.common.network_stat_utils import get_network_stat_legacy
from routingapp.common.models import *

# from routingapp.compare_algorithm.dijkstra.dijkstra_solver import dijkstra_solver
from routingapp.compare_algorithm.nsga_ii_origin.nsga_ii_origin_solver import nsga_ii_origin_solver
# from routingapp.compare_algorithm.nsga_iii import ?

from routingapp.compare_algorithm.gamr.gamr_solver import gamr_solver
from routingapp.compare_algorithm.gamr.module_memset import MemSet

from fastapi import APIRouter

router = APIRouter()

memset = MemSet()

# @router.post('/routing/dijkstra')
# async def routing_dijkstra(task: RouteTasks):
    # '''
        # Dijkstra algorithm routing
    # '''
    # return dijkstra_solver(task, legacy_get_network_stat())

@router.post('/routing/gamr')
async def gamr(task: MultiRouteTasks):
    '''
        GAMR routing algorithm
    '''
    return gamr_solver(task, memset, get_network_stat_legacy())

@router.post('/routing/nsga2_origin')
async def nsga2_origin(task: MultiRouteTasks):
    '''
        nsga2_origin algorithm
    '''
    return nsga_ii_origin_solver(task, get_network_stat_legacy())

@router.post('/routing/nsga3')
async def nsga3():
    '''
        nsga-iii algorithm
    '''
    # return 
