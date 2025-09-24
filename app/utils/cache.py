from flask_caching import Cache

# Configure the cache
# For simplicity, we'll start with a SimpleCache, which caches in memory.
# For production, you would likely want to use a more robust cache like Redis or Memcached.
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # Default timeout 5 minutes
})
