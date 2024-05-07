from pydantic import BaseModel

class RouteTask(BaseModel):
    '''
        Single Route Task Request
        for algorithm
    '''
    src_host: int
    dst_host: int

class MultiRouteTasks(BaseModel):
    route: list[RouteTask]

class ManualRoute(BaseModel):
    src_host: int
    dst_host: int
    path_dpid: list[int]

class ManualRouteTasks(BaseModel):
    route: list[ManualRoute]