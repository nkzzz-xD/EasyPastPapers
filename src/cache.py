from collections import OrderedDict

class PageCache:
    def __init__(self, max_cache_size=20):
        self._cache = OrderedDict()
        self.max_cache_size = max_cache_size

    def get(self, key):
        result = self._cache.get(key)
        self._cache.move_to_end(key)
        return result

    def set(self, key, value):
        self._cache[key] = value
        if len(self._cache) > self.max_cache_size:
            self._cache.popitem(last = False)

    def clear(self):
        self._cache.clear()

    def __contains__(self, key):
        return key in self._cache

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)