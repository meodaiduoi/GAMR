from routingapp.common.routing_utils import *
from routingapp.common.models import *

from extras.network_info_utils import n
from routingapp.compare_algorithm.dijkstra.dijkstra_solver import dijkstra_solver
from routingapp.config import Setting
from fastapi import APIRouter

router = APIRouter()

@router.post('/manual')
async def routing_manual(tasks: ManualRouteTasks):
    '''
    Manual routing \n
    '''
    
    network_stat = get_netw()
    setting = Setting()
    graph = network_stat.graph
    
    flowrules = []
    for task in tasks.route:
        path = [task.src_host] + task.path_dpid + [task.dst_host]
        task.model_dump()
        if nx.is_path(graph, task.path_dpid):
            flowrules.append(create_flowrule_json(task.model_dump(), get_host(), get_link_to_port()))
    return send_flowrule_single(flowrules, ryu_rest_port=setting.RYU_PORT)

@router.post('/min_hop')
async def routing_min_hop(tasks: MultiRouteTasks):
    '''
    Min-hop routing \n
    '''

    network_stat = get_network_stat_single()
    setting = Setting()
    graph = network_stat.graph
    solutions = {'route': []}
    flowrules = []
    for task in tasks.route:
        if nx.has_path(graph, f'h{task.src_host}', f'h{task.dst_host}'):
            path = list(nx.shortest_path(graph, f'h{task.src_host}', f'h{task.dst_host}'))
            solutions['route'].append({
                'src_host': task.src_host,
                'dst_host': task.dst_host,
                'path_dpid': path[1:-1],
            })
            flowrules = create_flowrule_json(solutions, get_host(), get_link_to_port())
    return send_flowrule_single(flowrules, ryu_rest_port=setting.RYU_PORT)

@router.post('/dijkstra')
async def routing_dijkstra(task: MultiRouteTasks):
    '''
        Dijkstra algorithm routing
    '''
    return send_flowrule_single(dijkstra_solver(task, get_network_stat_single()))

@router.get('/add_flow_all')
async def add_flow_all():
    '''
        Not yet implemented
    '''
    return