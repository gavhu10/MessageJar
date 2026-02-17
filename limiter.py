from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redislite import StrictRedis


redis = StrictRedis("/dev/shm/cache.rdb")

# From the docs:
# https://flask-limiter.readthedocs.io/en/stable/configuration.html#rate-limit-string-notation

# Rate limits are specified as strings following the format:

# [count] [per|/] [n (optional)] [second|minute|hour|day|month|year][s]
# You can combine multiple rate limits by separating them with a delimiter of your choice.

limiter = Limiter(
    get_remote_address,
    storage_uri=f"redis+unix://{redis.socket_file}",
)
