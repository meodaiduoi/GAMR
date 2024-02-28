class MemSet:
    def __init__(self):
        self.memset = {}
        #server_set includes server_node that having past router
        self.server_set = set()
    # A path includes routing and destination server
    # path_set includes paths to server (client, server, router)
    def addPath(self, path):
        if path not in self.memset[path[1]]:
            self.memset[path[1]].append(path)
        self.server_set.add(path[1])
    
    def addAllPath(self, solutions, pair_list):
        for pair in pair_list:
            self.memset[pair[1]] = []
        for indi in solutions:
            for path in indi.chromosome:
                self.addPath(path)
            