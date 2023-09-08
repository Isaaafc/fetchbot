from abc import ABC, abstractmethod
from typing import Any, Dict

from redis import Redis

class IDataStore(ABC):
    """
    Data store interface
    """

    @abstractmethod
    def get(self, key: str) -> str:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> bool:
        pass

class InMemoryDataStore(IDataStore):
    def __init__(self) -> None:
        self.__data: Dict[str, str] = dict()

    def get(self, key: str) -> str:
        return self.__data.get(key)

    def set(self, key: str, value: str) -> bool:
        self.__data[key] = value
        return True

class RedisDataStore(IDataStore):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.__redis_db = Redis(config['host'], config['port'], db=config['db'])

    def get(self, key: str) -> str:
        value = self.__redis_db.get(key)

        if value is not None:
            return value.decode('utf-8')

        return value

    def set(self, key: str, value: str) -> bool:
        return self.__redis_db.set(key, value)
