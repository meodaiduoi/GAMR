from pydantic import BaseModel

# class Task(BaseModel):
#     '''
#         src_ip: ip of
#     '''
#     src_ip: str
#     dst_ip: str
#     size: int | None = '10'
#     task: str | None = 'download'

class Ping(BaseModel):
    hostname_list: list[str] 
    timeout: str | None = None

class PingSingle(BaseModel):
    src_hostname: str
    dst_hostname: str
    timeout: float
    count: int

class Pingall(BaseModel):
    timeout: str | None = None

class PopenTask(BaseModel):
    hostname: str
    cmd: str
    wait: bool

class CmdTask(BaseModel):
    hostname: str
    cmd: str

class ConfigLink(BaseModel):
    '''
        name_node1: name of node1
        name_node2: name of node2
        status: status of link (up/down)
    '''
    name_node1: str
    name_node2: str
    status: str | None = 'up'
    