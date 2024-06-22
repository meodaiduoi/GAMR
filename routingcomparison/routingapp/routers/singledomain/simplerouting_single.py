from routingapp.common.routing_utils import *
from routingapp.common.models import *

from extras.network_info_utils import get_network_stat_single
from extras.network_unit_utils import get_host, get_link_to_port

from routingapp.compare_algorithm.dijkstra.dijkstra_solver import dijkstra_solver
from routingapp.compare_algorithm.ec_min_hop.min_hop_solver import min_hop_solver

from routingapp.config import Setting
from fastapi import APIRouter

import random
router = APIRouter()

@router.post('/manual')
async def routing_manual(tasks: ManualRouteTasks):
    '''
    Manual routing \n
    '''
    
    network_stat = get_network_stat_single()
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

@router.post('/random')
async def routing_random(tasks: MultiRouteTasks):
  """
  Random routing algorithm
  """
  network_stat = get_network_stat_single()
  graph = network_stat.graph
  solutions = {'route': []}
  flowrules = []
  for task in tasks.route:
    if nx.is_connected(graph):  # Check if network is connected before routing
      # Find all possible paths between source and destination
      all_paths = list(nx.all_shortest_paths(graph, f'h{task.src_host}', f'h{task.dst_host}'))
      # Choose a random path from all possible ones
      if all_paths:
        random_path = random.choice(all_paths)
        solutions['route'].append({
          'src_host': task.src_host,
          'dst_host': task.dst_host,
          'path_dpid': random_path[1:-1],
        })
        flowrules = create_flowrule_json(solutions, get_host(), get_link_to_port())
  return send_flowrule_single(flowrules, ryu_rest_port=Setting().RYU_PORT)

@router.post('/ec_min_hop')
async def routing_ec_min_hop(tasks: MultiRouteTasks):
    '''
        EC Min-hop routing \n
        for edge and cloud implementation
    '''
    return send_flowrule_single(
        min_hop_solver(tasks, get_network_stat_single()), ryu_rest_port=Setting().RYU_PORT)