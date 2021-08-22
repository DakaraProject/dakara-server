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
def debug(settings):
    settings.DEBUG = True


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


class TestCacheModel:
    def test_init(self, debug):
        """Test to create cache model instance"""
        dummy = Dummy()

        assert dummy.id is None
        assert hasattr(dummy, "boolean_field")
        assert dummy.boolean_field is False
        assert hasattr(dummy, "integer_field")
        assert dummy.integer_field == 0
        assert hasattr(dummy, "text_field")
        assert dummy.text_field is None

    def test_init_var(self, debug):
        """Test to create cache model instance with arguments"""
        dummy = Dummy(True, text_field="text", integer_field=2)

        assert dummy.id is None
        assert dummy.boolean_field is True
        assert dummy.integer_field == 2
        assert dummy.text_field == "text"

    def test_representation(self, debug):
        """Test to represent cache model instance"""
        assert repr(Dummy()) == "<Dummy: None>"

    def test_equality(self, debug):
        """Test to check two cache model instances"""
        dummy_1 = Dummy(integer_field=1)
        dummy_2 = Dummy(integer_field=1)

        assert dummy_1 == dummy_2

        dummy_3 = Dummy(integer_field=3)

        assert dummy_1 != dummy_3

    def test_save(self, debug, clear_cache):
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

    def test_delete(self, debug, clear_cache):
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


class TestCacheManager:
    def test_class_name(self, debug, clear_cache):
        """Test class name"""
        assert Dummy.__name__ == "Dummy"
        assert Dummy.objects.model.__name__ == "Dummy"

    def test_create(self, debug, clear_cache):
        """Test to create a cache model instance"""
        dummy = Dummy.objects.create()

        assert isinstance(dummy, Dummy)
        assert dummy.id == 1

    def test_all(self, debug, set_cache, clear_cache):
        """Test to get all cache model instances"""
        objects = Dummy.objects.all()
        assert len(objects) == 3
        assert isinstance(objects[0], Dummy)
        assert objects[0].id == 1
        assert isinstance(objects[1], Dummy)
        assert objects[1].id == 2
        assert isinstance(objects[2], Dummy)
        assert objects[2].id == 3

    def test_filter(self, debug, set_cache, clear_cache):
        """Test to query cache model instances"""
        assert len(Dummy.objects.filter(boolean_field=True)) == 3
        assert len(Dummy.objects.filter(integer_field=42)) == 2
        assert len(Dummy.objects.filter(text_field="baz")) == 1

    def test_get(self, debug, set_cache, clear_cache):
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

    def test_objects_get_or_create(self, debug, clear_cache):
        """Test to create cache model then get it"""
        dummy, created = Dummy.objects.get_or_create(id=1)

        assert dummy.id == 1
        assert created

        dummy.save()
        del dummy

        dummy, created = Dummy.objects.get_or_create(id=1)

        assert dummy.id == 1
        assert not created
