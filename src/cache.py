from collections import OrderedDict
from typing import Any

class PageCache:
    """
    A simple LRU (Least Recently Used) cache for storing HTML pages.

    This cache is used to store a limited number of parsed HTML pages 
    to avoid redundant network requests and parsing, improving performance when accessing
    the same resources multiple times.

    Attributes:
        max_cache_size (int): The maximum number of items to store in the cache.
    """
    
    def __init__(self, max_cache_size: int = 20) -> None:
        """
        Initialize the PageCache.

        Args:
            max_cache_size (int): Maximum number of items to keep in the cache.
        """
        if max_cache_size <= 0:
            raise ValueError("max_cache_size must be a positive integer.")
        if not isinstance(max_cache_size, int):
            raise TypeError("max_cache_size must be an integer.")
        self._cache: OrderedDict[Any, Any] = OrderedDict()
        self.max_cache_size: int = max_cache_size

    def get(self, key: Any) -> Any:
        """
        Retrieve an item from the cache and mark it as recently used.
        Args:
            key: The key to look up in the cache.
        Returns:
            The cached value if present, else None.
        """
        result = self._cache.get(key)
        self._cache.move_to_end(key)
        return result

    def set(self, key: Any, value: Any) -> None:
        """
        Add or update an item in the cache. If the cache exceeds its maximum size,
        the least recently used item is removed.
        Args:
            key: The key to store the value under.
            value: The value to cache.
        """
        self._cache[key] = value
        if len(self._cache) > self.max_cache_size:
            self._cache.popitem(last = False)

    def clear(self) -> None:
        """
        Remove all items from the cache.
        """
        self._cache.clear()

    def __contains__(self, key: Any) -> bool:
        """
        Check if a key exists in the cache.
        Args:
            key: The key to check.
        Returns:
            bool: True if key is in the cache, False otherwise.
        """
        return key in self._cache

    def __getitem__(self, key: Any) -> Any:
        """
        Retrieve an item using the [] operator.
        Args:
            key: The key to look up.
        Returns:
            The cached value if present, else None.
        """
        return self.get(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Set an item using the [] operator.
        Args:
            key: The key to store the value under.
            value: The value to cache.
        """
        self.set(key, value)