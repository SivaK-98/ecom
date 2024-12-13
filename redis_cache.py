"""Basic connection example.
"""

import redis

r = redis.Redis(
    host='redis-16735.c301.ap-south-1-1.ec2.redns.redis-cloud.com',
    port=16735,
    decode_responses=True,
    username="default",
    password="8AmM5jAaVNKRi2tYnLMxJUm2yt718Zcv",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar
