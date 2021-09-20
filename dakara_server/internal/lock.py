from django.core.cache import cache
from django.core.cache.backends.db import BaseDatabaseCache
from django.core.cache.backends.memcached import BaseMemcachedCache
from django_lock import Lock, MemcachedLock, RedisLock, _backend_cls, redis_backends


def get_lock_cls(client):
    """Monkey patch the cache backend selector of django_lock"""
    backend_cls = _backend_cls(client)
    if issubclass(backend_cls, redis_backends):
        return RedisLock

    if issubclass(backend_cls, BaseMemcachedCache):
        return MemcachedLock

    if issubclass(backend_cls, BaseDatabaseCache):
        raise NotImplementedError("Database cache not supported")

    return Lock


def lock(name, client=None, **kwargs):
    """Monkey patch the lock function of django_lock"""
    client = client or cache
    lock_cls = get_lock_cls(client)
    return lock_cls(name, client, **kwargs)
