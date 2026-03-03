import os
import fastf1

DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")


def enable_cache(cache_dir: str = None) -> str:
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)
    return cache_dir
