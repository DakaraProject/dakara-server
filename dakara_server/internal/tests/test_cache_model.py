from re import escape

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
    Dummy.cache.create(boolean_field=True, integer_field=42, text_field="foo")
    Dummy.cache.create(boolean_field=True, integer_field=42, text_field="bar")
    Dummy.cache.create(boolean_field=True, integer_field=39, text_field="baz")


class Dummy(CacheModel):
    """Dummy model used for tests"""

    boolean_field = models.BooleanField(default=False)
    integer_field = models.IntegerField(default=0)
    text_field = models.CharField(max_length=255, null=True)

    def __str__(self):
        return "Dummy object"


class DummyAuto(CacheModel):
    """Dummy model with auto updated fields used for tests"""

    datetime_field = models.DateTimeField(auto_now=True)
    date_field = models.DateField(auto_now=True)
    time_field = models.TimeField(auto_now=True)

    def __str__(self):
        return "Dummy auto object"


class TestCacheModel:
    def test_init(self):
        """Test to create cache model instance"""
        dummy = Dummy()

        assert hasattr(dummy, "pk")
        assert dummy.pk is None
        assert hasattr(dummy, "id")
        assert dummy.id is None
        assert dummy.id is dummy.pk
        assert hasattr(dummy, "boolean_field")
        assert dummy.boolean_field is False
        assert hasattr(dummy, "integer_field")
        assert dummy.integer_field == 0
        assert hasattr(dummy, "text_field")
        assert dummy.text_field is None

    def test_init_var(self):
        """Test to create cache model instance with arguments"""
        dummy = Dummy(boolean_field=True, text_field="text", integer_field=2)

        assert dummy.pk is None
        assert dummy.boolean_field is True
        assert dummy.integer_field == 2
        assert dummy.text_field == "text"

    def test_save(self, clear_cache):
        """Test to save cache models"""
        dummy_cache = cache.get(Dummy.cache._store_name)
        assert dummy_cache is None

        dummy_1 = Dummy()
        dummy_1.save()
        dummy_2 = Dummy()
        dummy_2.save()

        assert dummy_1.pk == 1
        assert dummy_1.id == 1
        assert dummy_2.pk == 2
        assert dummy_2.id == 2

        # check object is in cache
        dummy_cache = cache.get(Dummy.cache._store_name)
        assert len(dummy_cache) == 2

    def test_delete(self, clear_cache):
        """Test to delete a cache model"""
        dummy_cache = cache.get(Dummy.cache._store_name)
        assert dummy_cache is None

        dummy_1 = Dummy()
        dummy_1.save()
        dummy_2 = Dummy()
        dummy_2.save()
        dummy_1.delete()

        # check object is not in cache
        dummy_cache = cache.get(Dummy.cache._store_name)
        assert len(dummy_cache) == 1
        assert 2 in dummy_cache

    def test_delete_not_saved(self, clear_cache):
        """Test to delete a cache model not saved in cache"""
        dummy = Dummy()
        with pytest.raises(
            ObjectDoesNotExist, match=r"Dummy object does not exist in cache yet"
        ):
            dummy.delete()

    def test_auto_model(self, clear_cache):
        """Test fields that can be automatically updated"""
        # create object and set fields
        dummy = DummyAuto()

        # assert no fields are set
        assert dummy.datetime_field is None
        assert dummy.date_field is None
        assert dummy.time_field is None

        # save object
        dummy.save()

        # check fields are now automatically set
        assert dummy.datetime_field is not None
        assert dummy.date_field is not None
        assert dummy.time_field is not None


class TestCacheManager:
    def test_class_name(self, clear_cache):
        """Test class name"""
        assert Dummy.__name__ == "Dummy"
        assert Dummy.cache.model.__name__ == "Dummy"

    def test_attributes(self, clear_cache):
        """Test attributes of the manager"""
        assert Dummy.cache.model is Dummy
        assert Dummy.cache.name == "Dummy"
        assert Dummy.cache._store_name == "Dummy:CacheStore"
        assert DummyAuto.cache.model is DummyAuto

    def test_create(self, clear_cache):
        """Test to create a cache model instance"""
        dummy = Dummy.cache.create()

        assert isinstance(dummy, Dummy)
        assert dummy.pk == 1

    def test_create_already_exists(self, clear_cache):
        """Test to create a cache model instance that already exists"""
        dummy = Dummy.cache.create(pk=1, boolean_field=True)
        dummy_new = Dummy.cache.create(pk=1)

        assert dummy.pk == dummy_new.pk
        assert not dummy_new.boolean_field

    def test_all(self, set_cache, clear_cache):
        """Test to get all cache model instances"""
        objects = Dummy.cache.all()
        assert len(objects) == 3
        assert isinstance(objects[0], Dummy)
        assert objects[0].pk == 1
        assert isinstance(objects[1], Dummy)
        assert objects[1].pk == 2
        assert isinstance(objects[2], Dummy)
        assert objects[2].pk == 3

    def test_filter(self, set_cache, clear_cache):
        """Test to query cache model instances"""
        assert len(Dummy.cache.filter(boolean_field=True)) == 3
        assert len(Dummy.cache.filter(integer_field=42)) == 2
        assert len(Dummy.cache.filter(text_field="baz")) == 1

    def test_get(self, set_cache, clear_cache):
        """Test to get a specific cache model instance"""
        with pytest.raises(
            ObjectDoesNotExist, match="Dummy matching query does not exist"
        ):
            Dummy.cache.get(integer_field=43)

        with pytest.raises(
            MultipleObjectsReturned,
            match=escape("get() returned more than one Dummy -- it returned 2!"),
        ):
            Dummy.cache.get(integer_field=42)

        Dummy.cache.get(integer_field=39)

    def test_get_or_create(self, clear_cache):
        """Test to get or create cache model"""
        dummy, created = Dummy.cache.get_or_create(pk=1)

        assert dummy.pk == 1
        assert created

        dummy.save()
        del dummy

        dummy, created = Dummy.cache.get_or_create(pk=1)

        assert dummy.pk == 1
        assert not created

    def test_get_or_create_default(self, clear_cache):
        """Test to get or create cache model with default value"""
        dummy, created = Dummy.cache.get_or_create(pk=1, defaults={"integer_field": 42})

        assert dummy.pk == 1
        assert dummy.integer_field == 42
        assert created

        dummy.save()
        del dummy

        dummy, created = Dummy.cache.get_or_create(pk=1, defaults={"integer_field": 43})

        assert dummy.pk == 1
        assert dummy.integer_field == 42
        assert not created

    def test_save_extra(self, clear_cache):
        """Test to save cache model with extra fields"""
        dummy = Dummy()
        dummy.not_a_field = True
        dummy.save()

        # assert extra field is present
        assert hasattr(dummy, "not_a_field")

        pk = dummy.pk
        del dummy
        dummy = Dummy.cache.get(pk=pk)

        # assert extra field is absent
        assert not hasattr(dummy, "not_a_field")
