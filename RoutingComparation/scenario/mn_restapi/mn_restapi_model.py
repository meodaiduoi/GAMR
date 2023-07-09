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
    time: int | None = 10

class Command(BaseModel):
    host_name: str
    cmd: str
    wait: bool