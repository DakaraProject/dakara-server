from unittest.mock import MagicMock

import pytest
from django.core.cache import cache
from django.core.cache.backends.db import BaseDatabaseCache
from django.core.cache.backends.memcached import BaseMemcachedCache

from internal import lock


class TestGetLockCls:
    def test_redis(self, mocker):
        """Test to get the Redis lock"""

        class BaseRedisBackend:
            pass

        class RedisBackend(BaseRedisBackend):
            pass

        mocker.patch("internal.lock.redis_backends", (BaseRedisBackend,))
        mocked_backend_cls = mocker.patch("internal.lock._backend_cls")
        mocked_backend_cls.return_value = RedisBackend

        assert lock.get_lock_cls(MagicMock()) is lock.RedisLock

    def test_memcached(self, mocker):
        """Test to get the Memcached lock"""

        class MemcachedCache(BaseMemcachedCache):
            pass

        mocked_backend_cls = mocker.patch("internal.lock._backend_cls")
        mocked_backend_cls.return_value = MemcachedCache

        assert lock.get_lock_cls(MagicMock()) is lock.MemcachedLock

    def test_database(self, mocker):
        """Test to get the Database lock"""

        class DatabaseCache(BaseDatabaseCache):
            pass

        mocked_backend_cls = mocker.patch("internal.lock._backend_cls")
        mocked_backend_cls.return_value = DatabaseCache

        with pytest.raises(NotImplementedError):
            lock.get_lock_cls(MagicMock())

    def test_(self, mocker):
        """Test to get the normal lock"""

        class OtherCache:
            pass

        mocked_backend_cls = mocker.patch("internal.lock._backend_cls")
        mocked_backend_cls.return_value = OtherCache

        assert lock.get_lock_cls(MagicMock()) is lock.Lock


class TestLock:
    def test_get(self, mocker):
        """Test to get a lock without arguments"""
        mocked_get_lock_cls = mocker.patch("internal.lock.get_lock_cls")

        lock.lock("name")

        mocked_get_lock_cls.assert_called_with(cache)
        mocked_get_lock_cls.return_value.assert_called_with("name", cache)

    def test_get_client(self, mocker):
        """Test to get a lock with a specific client"""
        client = MagicMock()
        mocked_get_lock_cls = mocker.patch("internal.lock.get_lock_cls")

        lock.lock("name", client)

        mocked_get_lock_cls.assert_called_with(client)
        mocked_get_lock_cls.return_value.assert_called_with("name", client)
