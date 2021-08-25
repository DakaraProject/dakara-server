from re import escape
from datetime import datetime

import pytest
from django.db import models
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from internal.cache_model import CacheModel


@pytest.fixture
def clear_cache():
    yield None
    cache.clear()


@pytest.fixture
def set_cache():
    Dummy.objects.create(boolean_field=True, integer_field=42, text_field="foo")
    Dummy.objects.create(boolean_field=True, integer_field=42, text_field="bar")
    Dummy.objects.create(boolean_field=True, integer_field=39, text_field="baz")


class Dummy(CacheModel):
    """Dummy model used for tests"""

    boolean_field = models.BooleanField(default=False)
    integer_field = models.IntegerField(default=0)
    text_field = models.CharField(max_length=255, null=True)


class DummyAuto(CacheModel):
    """Dummy model with auto updated fields used for tests"""

    datetime_field = models.DateTimeField(auto_now=True, auto_now_add=True)
    date_field = models.DateField(auto_now=True, auto_now_add=True)
    time_field = models.TimeField(auto_now=True, auto_now_add=True)


class TestCacheModel:
    def test_init(self):
        """Test to create cache model instance"""
        dummy = Dummy()

        assert dummy.id is None
        assert hasattr(dummy, "boolean_field")
        assert dummy.boolean_field is False
        assert hasattr(dummy, "integer_field")
        assert dummy.integer_field == 0
        assert hasattr(dummy, "text_field")
        assert dummy.text_field is None

    def test_init_var(self):
        """Test to create cache model instance with arguments"""
        dummy = Dummy(True, text_field="text", integer_field=2)

        assert dummy.id is None
        assert dummy.boolean_field is True
        assert dummy.integer_field == 2
        assert dummy.text_field == "text"

    def test_representation(self):
        """Test to represent cache model instance"""
        assert repr(Dummy()) == "<Dummy: None>"

    def test_equality(self):
        """Test to check two cache model instances"""
        dummy_1 = Dummy(integer_field=1)
        dummy_2 = Dummy(integer_field=1)

        assert dummy_1 == dummy_2

        dummy_3 = Dummy(integer_field=3)

        assert dummy_1 != dummy_3

    def test_save(self, clear_cache):
        """Test to save cache models"""
        dummy_cache = cache.get(Dummy.objects._store_name)
        assert dummy_cache is None

        dummy_1 = Dummy()
        dummy_1.save()
        dummy_2 = Dummy()
        dummy_2.save()

        assert dummy_1.id == 1
        assert dummy_2.id == 2

        # check object is in cache
        dummy_cache = cache.get(Dummy.objects._store_name)
        assert len(dummy_cache) == 2

    def test_delete(self, clear_cache):
        """Test to delete a cache model"""
        dummy_cache = cache.get(Dummy.objects._store_name)
        assert dummy_cache is None

        dummy_1 = Dummy()
        dummy_1.save()
        dummy_2 = Dummy()
        dummy_2.save()
        dummy_1.delete()

        # check object is in cache
        dummy_cache = cache.get(Dummy.objects._store_name)
        assert len(dummy_cache) == 1
        assert 2 in dummy_cache

    def test_auto_model(self, clear_cache, mocker):
        """Test fields that can be automatically updated"""
        # setup mock
        mocked_datetime = mocker.patch("internal.cache_model.datetime")
        mocked_datetime.now.side_effect = [
            datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0),
            datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0),
            datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0),
            datetime(year=1971, month=1, day=1, hour=0, minute=0, second=1),
            datetime(year=1971, month=1, day=1, hour=0, minute=0, second=1),
            datetime(year=1971, month=1, day=1, hour=0, minute=0, second=1),
        ]

        # create object and set fields
        dummy = DummyAuto()

        # check fields are automatically set
        assert dummy.datetime_field is not None
        assert dummy.date_field is not None
        assert dummy.time_field is not None

        old_datetime = dummy.datetime_field
        old_date = dummy.date_field
        old_time = dummy.time_field

        # save object and set fields again
        dummy.save()

        # check fields are automatically set again
        assert dummy.datetime_field is not None
        assert dummy.date_field is not None
        assert dummy.time_field is not None
        assert dummy.datetime_field != old_datetime
        assert dummy.date_field != old_date
        assert dummy.time_field != old_time


class TestCacheManager:
    def test_class_name(self, clear_cache):
        """Test class name"""
        assert Dummy.__name__ == "Dummy"
        assert Dummy.objects.model.__name__ == "Dummy"

    def test_attributes(self, clear_cache):
        """Test attributes of the manager"""
        assert Dummy.objects.model is Dummy
        assert Dummy.objects.name == "Dummy"
        assert Dummy.objects._store_name == "Dummy:CacheStore"

    def test_create(self, clear_cache):
        """Test to create a cache model instance"""
        dummy = Dummy.objects.create()

        assert isinstance(dummy, Dummy)
        assert dummy.id == 1

    def test_create_already_exists(self, clear_cache):
        """Test to create a cache model instance that already exists"""
        dummy = Dummy.objects.create(id=1, boolean_field=True)
        dummy_new = Dummy.objects.create(id=1)

        assert dummy.id == dummy_new.id
        assert not dummy_new.boolean_field

    def test_all(self, set_cache, clear_cache):
        """Test to get all cache model instances"""
        objects = Dummy.objects.all()
        assert len(objects) == 3
        assert isinstance(objects[0], Dummy)
        assert objects[0].id == 1
        assert isinstance(objects[1], Dummy)
        assert objects[1].id == 2
        assert isinstance(objects[2], Dummy)
        assert objects[2].id == 3

    def test_filter(self, set_cache, clear_cache):
        """Test to query cache model instances"""
        assert len(Dummy.objects.filter(boolean_field=True)) == 3
        assert len(Dummy.objects.filter(integer_field=42)) == 2
        assert len(Dummy.objects.filter(text_field="baz")) == 1

    def test_get(self, set_cache, clear_cache):
        """Test to get a specific cache model instance"""
        with pytest.raises(
            ObjectDoesNotExist, match="Dummy matching query does not exist"
        ):
            Dummy.objects.get(integer_field=43)

        with pytest.raises(
            MultipleObjectsReturned,
            match=escape("get() returned more than one Dummy -- it returned 2!"),
        ):
            Dummy.objects.get(integer_field=42)

        Dummy.objects.get(integer_field=39)

    def test_objects_get_or_create(self, clear_cache):
        """Test to create cache model then get it"""
        dummy, created = Dummy.objects.get_or_create(id=1)

        assert dummy.id == 1
        assert created

        dummy.save()
        del dummy

        dummy, created = Dummy.objects.get_or_create(id=1)

        assert dummy.id == 1
        assert not created
