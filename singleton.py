########
# Singleton approximation to cache the network method
########

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NetworkCache(metaclass=Singleton):
    def __init__(self):
        self.__cache: dict = {}
        self.__forbid_cache: set = set()

    def remove_from_cache(self, hashed_id: str):
        self.__forbid_cache.add(hashed_id)

    def get_cached_value(self, hashed_id: str):
        if hashed_id in self.__forbid_cache or hashed_id not in self.__cache:
            return (False,)
        else:
            return True, self.__cache.get(hashed_id)

    # TODO, set un typing on the value
    def cache_value(self, hashed_id: str, to_cache_value: dict):
        if hashed_id in self.__forbid_cache:
            self.__forbid_cache.remove(hashed_id)
        self.__cache[hashed_id] = to_cache_value

    def get_cache(self):
        return self.__cache
