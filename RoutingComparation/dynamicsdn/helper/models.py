from pydantic import BaseModel

class SrcDst(BaseModel):
    src_host: int
    dst_host: int

class RouteTasks(BaseModel):
    route: list[SrcDst]

class ManualRoute(BaseModel):
    src_host: int
    dst_host: int
    path_dpid: list[int]

class ManualRouteTasks(BaseModel):
    route: list[ManualRoute]