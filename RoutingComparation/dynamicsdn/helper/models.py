from pydantic import BaseModel

class SrcDst(BaseModel):
    src_host: int
    dst_host: int

class RouteTask(BaseModel):
    route: list[SrcDst]
    

class ManualRoute(BaseModel):
    src_host: int
    dst_host: int
    path: list[int]

class ManualRouteTask(BaseModel):
    route: list[ManualRoute]