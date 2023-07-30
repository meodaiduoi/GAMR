from collections import defaultdict
import networkx as nx
import random

class SpanningTree:
    def __init__(self, graph, number_tree=1):
        self.graph = graph
        self.number_tree = number_tree
    
    def _add_edge(self, graph, u, v):
        graph[u].append(v)

    def _convert_to_undirected(self, graph):
        undirected_graph = defaultdict(list)
        for u in graph:
            for v in graph[u]:
                self._add_edge(undirected_graph, u, v)
                self._add_edge(undirected_graph, v, u)
        return undirected_graph

    def _dfs(self,graph, vertex, visited, spanning_tree):
        visited.add(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                spanning_tree[vertex].append(neighbor)
                self._dfs(graph, neighbor, visited, spanning_tree)

    def _find_spanning_tree(self,digraph, root):
        undirected_graph = self._convert_to_undirected(digraph)
        visited = set()
        spanning_tree = defaultdict(list)

        self._dfs(undirected_graph, root, visited, spanning_tree)
        return spanning_tree


    def solution(self) -> list[list[tuple]]:
        adj_list = {node: list(self.graph.successors(node)) for node in self.graph.nodes()}
        node_list = list(self.graph.nodes())
        path_list = []
        for i in range(self.number_tree):
            path_tree = []
            for adjance in adj_list.values():
                random.shuffle(adjance)
            spanning_tree = self._find_spanning_tree(adj_list, node_list[i])
            for u in spanning_tree:
                u_list = spanning_tree[u]
                for v in u_list:
                    path_tree.append((u,v))
            path_list.append(path_tree)
        
        return path_list
    
    def solution_invert(self) -> list[list[tuple]]:
        path_list = self.solution()
        edges = self.graph.edges()
        invert_list = []
        for path in path_list:
            invert_path = []
            for edge in edges:
                if ((edge[0], edge[1]) not in path) and ((edge[1], edge[0]) not in path) and ((edge[0], edge[1]) not in invert_path) and ((edge[1], edge[0]) not in invert_path):
                    invert_path.append(edge)
            invert_list.append(invert_path)
        return invert_list
    
    def solution_as_networkx(self) -> nx.Graph:
        path_list = self.solution()
        graph = nx.Graph()
        for path in path_list:
            for edge in path:
                graph.add_edge(edge[0], edge[1])
        return graph
    
        
def convert_network(net):
    '''
        converting Mininet network to networkx graph
    '''
    graph = nx.DiGraph()
    for link in net.links:
         # Add edges to the graph
        src = link.intf1.node.name
        dst = link.intf2.node.name
        graph.add_edge(src, dst)
        graph.add_edge(dst, src)
    return graph