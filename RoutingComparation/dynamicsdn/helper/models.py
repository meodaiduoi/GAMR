from pydantic import BaseModel

class SrcDst(BaseModel):
    src_host: int
    dst_host: int

class RouteTask(BaseModel):
    route: list[SrcDst]