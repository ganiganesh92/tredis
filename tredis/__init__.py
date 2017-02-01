"""
TRedis
======
An asynchronous Redis client for Tornado

"""
from tredis.client import Client, RedisClient
from tredis import exceptions
from tredis.strings import BITOP_AND, BITOP_OR, BITOP_XOR, BITOP_NOT

__version__ = '0.6.0'
