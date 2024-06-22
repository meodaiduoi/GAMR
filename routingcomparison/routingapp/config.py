from pydantic_settings import BaseSettings
import os

class Setting(BaseSettings):
    ROUTING_APP_PORT: int = int(os.environ.get('ROUTING_APP_PORT'))
    RYU_PORT: int = int(os.environ.get('RYU_PORT'))
    RESTHOOKMN_PORT: int = os.environ.get('RESTHOOKMN_PORT')
    MULTI_DOMAIN: bool = bool(os.environ.get('MULTI_DOMAIN'))
    OFP_PORT: int = int(os.environ.get('OFP_PORT'))