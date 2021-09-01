from contextlib import contextmanager

from django.core.cache import cache
from django.db.models import base

from internal.lock import lock


class CacheManager:
    """Manage objects in cache"""

    def __init__(self):
        self.model = None
        self.name = None
        self._store_name = None

    def _connect(self, model):
        """Associate a model with the manager

        Args:
            model (CacheModel): Model to connect.
        """
        self.model = model
        self.name = model.__name__
        self._store_name = f"{self.model.__name__}:CacheStore"

    @contextmanager
    def _access_store(self):
        """Give read/write access to the store in cache

        Access to the cache is locked to avoid race conditions.

        Yields:
            dict: Store containing all instances of the managed model, their ID
            is used as key.
        """
        with lock(self._store_name):
            store = cache.get(self._store_name, {})
            yield store
            cache.set(self._store_name, store)

    def create(self, *args, **kwargs):
        """Create a managed model instance and save it

        Returns:
            CacheModel: Instance of the managed model.
        """
        obj = self.model(*args, **kwargs)
        obj.save()
        return obj

    def all(self):
        """Give all instances in cache of the managed model

        Returns:
            list: List of instances.
        """
        with self._access_store() as store:
            return list(store.values())

    def filter(self, **kwargs):
        """Give instances of managed model matching provided criteria

        Returns:
            list: List of instances.
        """
        return [
            obj
            for obj in self.all()
            if all([getattr(obj, name) == value for name, value in kwargs.items()])
        ]

    def get(self, **kwargs):
        """Give the only instance of managed model matching provided criteria

        Returns:
            CacheModel: Instances.

        Raises:
            ObjectDoesNotExist: If no instances match the criteria.
            MultipleObjectsReturned: If more than 1 instances match the criteria.
        """
        objects = self.filter(**kwargs)

        if len(objects) == 1:
            return objects[0]

        if len(objects) == 0:
            raise self.model.DoesNotExist(
                f"{self.model.__name__} matching query does not exist"
            )

        raise self.model.MultipleObjectsReturned(
            f"get() returned more than one {self.model.__name__} -- "
            f"it returned {len(objects)}!"
        )

    def get_or_create(self, defaults=None, **kwargs):
        """Give or create the only instance  matching provided criteria

        Args:
            default (dict): Default values used to create the object.

        Returns:
            tuple: Instance and True if it had to be created, False if it
            already existed.
        """
        try:
            return self.get(**kwargs), False

        except self.model.DoesNotExist:
            # add default values
            if defaults:
                kwargs.update(defaults)

            return self.create(**kwargs), True


class CacheModelBase(base.ModelBase):
    """Metaclass to connect cache manager to model"""

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # create and connect cache manager
        manager = CacheManager()
        manager._connect(new_class)
        setattr(new_class, "cache", manager)

        return new_class


class CacheModel(base.Model, metaclass=CacheModelBase):
    """Model which instances only exist in cache"""

    class Meta:
        managed = False
        abstract = True

    def save(self, *args, **kwargs):
        """Save instance in cache"""
        # prepare fields
        for field in self._meta.concrete_fields:
            field.pre_save(self, None)

        with self.cache._access_store() as store:
            # manage ID
            if self.pk is None:
                self.pk = max(list(store.keys()) or [0]) + 1

            # set object in cache
            store[self.pk] = self

    def delete(self):
        """Delete instance from cache

        Raises:
            ObjectDoesNotExist: If called on an unsaved object.
        """
        # raise exception if object not in cache
        if self.pk is None:
            raise self.DoesNotExist(f"{self} does not exist in cache yet")

        with self.cache._access_store() as store:
            # delete object from cache
            del store[self.pk]
