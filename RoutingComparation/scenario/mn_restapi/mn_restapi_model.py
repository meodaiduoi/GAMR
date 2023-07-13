from pydantic import BaseModel

class Task(BaseModel):
    '''
        src_ip: ip of
    '''
    src_ip: str
    dst_ip: str
    size: int | None = '10'
    task: str | None = 'download'

class Ping(BaseModel):
    hostname_list: list[str] 
    timeout: str | None = None

class Pingall(BaseModel):
    timeout: str | None = None

class PopenTask(BaseModel):
    hostname: str
    cmd: str
    wait: bool

class CmdTask(BaseModel):
    hostname: str
    cmd: str
