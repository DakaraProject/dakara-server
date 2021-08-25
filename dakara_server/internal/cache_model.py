from contextlib import contextmanager
from datetime import datetime

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import fields
from django.utils import timezone

from internal.lock import lock

tz = timezone.get_default_timezone()


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
        """Give access to the store in cache

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

    def get_or_create(self, **kwargs):
        """Give or create the only instance  matching provided criteria

        Returns:
            tuple: Instance and True if it had to be created, False if it
            already existed.
        """
        try:
            return self.get(**kwargs), False

        except self.model.DoesNotExist:
            return self.create(**kwargs), True


class BaseCacheModel(type):
    """Metaclass to connect manager to model"""

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # initialize subclasses of the model
        parents = [base for base in bases if isinstance(base, BaseCacheModel)]
        if not parents:
            return new_class

        # create exceptions
        setattr(new_class, "DoesNotExist", ObjectDoesNotExist)
        setattr(new_class, "MultipleObjectsReturned", MultipleObjectsReturned)

        # create and connect manager
        manager = CacheManager()
        manager._connect(new_class)
        setattr(new_class, "objects", manager)

        return new_class


class CacheModel(metaclass=BaseCacheModel):
    """Model that instances only exist in cache"""

    id = fields.IntegerField(default=None)

    def __init__(self, *args, **kwargs):
        # create fields list
        self._fields = self._get_fields()

        # create attributes according to fields
        for name, field in self._fields:
            if isinstance(field, fields.DateTimeField) and field.auto_now_add:
                setattr(self, name, datetime.now(tz))

            elif isinstance(field, fields.DateField) and field.auto_now_add:
                setattr(self, name, datetime.now(tz).date())

            elif isinstance(field, fields.TimeField) and field.auto_now_add:
                setattr(self, name, datetime.now(tz).time())

            elif field.default == fields.NOT_PROVIDED:
                setattr(self, name, None)

            else:
                setattr(self, name, field.default)

        # set args
        for arg, (name, _) in zip(args, self._fields):
            setattr(self, name, arg)

        # set kwargs
        for name, arg in kwargs.items():
            setattr(self, name, arg)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self):
        return str(self.id)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(frozenset([getattr(self, name) for name, _ in self._fields]))

    @classmethod
    def _get_fields(cls):
        """List fields of the model

        Returns:
            list: List of tuples containing the name of the field and the field object.
        """
        return [
            (attr, getattr(cls, attr))
            for attr in dir(cls)
            if isinstance(getattr(cls, attr), fields.Field)
        ]

    def save(self):
        """Save instance in cache"""
        with self.objects._access_store() as store:
            # manage ID
            if self.id is None:
                self.id = max(list(store.keys()) or [0]) + 1

            # manage automatic fields
            for name, field in self._fields:
                if isinstance(field, fields.DateTimeField) and field.auto_now:
                    setattr(self, name, datetime.now(tz))

                elif isinstance(field, fields.DateField) and field.auto_now:
                    setattr(self, name, datetime.now(tz).date())

                elif isinstance(field, fields.TimeField) and field.auto_now:
                    setattr(self, name, datetime.now(tz).time())

            # set object in cache
            store[self.id] = self

    def delete(self):
        """Delete instance from cache"""
        with self.objects._access_store() as store:
            # delete object from cache
            del store[self.id]
