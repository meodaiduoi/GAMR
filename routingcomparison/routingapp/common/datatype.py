from dataclasses import dataclass
import networkx as nx

@dataclass
class NetworkGraph():
    mapping: dict
    graph: nx.Graph
    
@dataclass
class LaunchOpt:
    app_api_port: int
    ryu_port: int 

@dataclass
class NetworkStat:
    ...
