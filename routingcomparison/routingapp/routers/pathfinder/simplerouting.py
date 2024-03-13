from routingapp.common.routing_utils import *
from routingapp.common.models import *

from fastapi import APIRouter

router = APIRouter()

@router.post('/manual')
async def routing_manual(tasks: ManualRouteTasks):
    '''
    Manual routing \n
    '''

    flowrules = []
    for task in tasks.route:
        path = [task.src_host] + task.path_dpid + [task.dst_host]
        task.model_dump()
        if nx.is_path(GRAPH, task.path_dpid):
            flowrules.append(create_flowrule_json(task.model_dump(), get_host(), get_link_to_port()))
    return send_flowrule(flowrules, ryu_rest_port=RYU_PORT)

@router.post('/min_hop')
async def routing_min_hop(tasks: RouteTasks):
    '''
    Min-hop routing \n
    '''

    solutions = {'route': []}
    flowrules = []
    for task in tasks.route:
        if nx.has_path(GRAPH, f'h{task.src_host}', f'h{task.dst_host}'):
            path = list(nx.shortest_path(GRAPH, f'h{task.src_host}', f'h{task.dst_host}'))
            solutions['route'].append({
                'src_host': task.src_host,
                'dst_host': task.dst_host,
                'path_dpid': path[1:-1],
            })
            flowrules = create_flowrule_json(solutions, get_host(), get_link_to_port())
    return send_flowrule(flowrules, ryu_rest_port=RYU_PORT)

@router.post('/dijkstra')
async def routing_dijkstra(task: RouteTasks):
    '''
        Dijkstra algorithm routing
    '''
    return dijkstra_solver(task_serve(task))

@router.get('/add_flow_all')
async def add_flow_all():
    '''
        Not yet implemented
    '''
    return