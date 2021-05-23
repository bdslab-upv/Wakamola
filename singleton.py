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
        # TODO load the cached values
        self.cache: dict = {}
        self.forbid_cache: set = set()

    def remove_from_cache(self, hashed_id: str):
        self.forbid_cache.add(hashed_id)

    def get_cached_value(self, hashed_id: str):
        if hashed_id in self.forbid_cache:
            return (False,)
        else:
            return True, self.cache.get(hashed_id)

    # TODO, set un typing on the value
    def cache_value(self, hashed_id: str, to_cache_value):
        if hashed_id in self.forbid_cache:
            self.forbid_cache.remove(hashed_id)
        self.cache[hashed_id] = to_cache_value


