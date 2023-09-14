from fastapi import APIRouter

router = APIRouter()

@router.get('/test')
async def test():
    '''
        get lists of all hostname and switchname \n
    '''
    host_names = [host.name for host in net.hosts]
    switch_names = [switch.name for switch in net.switches]
    return {
        'hostname': host_names,
        'switchname': switch_names
    }