from routingapp.common.routing_utils import *
from routingapp.common.network_stat_utils import get_network_stat_legacy
from routingapp.common.models import *

from routingapp.compare_algorithm.sec_morl_multipolicy.sec_solver import sec_solver

from fastapi import APIRouter

router = APIRouter()


@router.post('/dijkstra')
async def routing_dijkstra(task: RouteTask):
    '''
        Dijkstra algorithm routing
    '''
    return sec_solver(task, get_network_stat_legacy())