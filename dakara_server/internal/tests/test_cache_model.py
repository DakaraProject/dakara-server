from re import escape

import pytest
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import models

from internal import cache_model
from internal.tests.models import Reference


@pytest.fixture
def clear_cache():
    yield None
    cache.clear()


@pytest.fixture
def set_cache():
    Dummy.cache.create(boolean_field=True, integer_field=42, text_field="foo")
    Dummy.cache.create(boolean_field=True, integer_field=42, text_field="bar")
    Dummy.cache.create(boolean_field=True, integer_field=39, text_field="baz")


class Dummy(cache_model.CacheModel):
    """Dummy model used for tests"""

    boolean_field = models.BooleanField(default=False)
    integer_field = models.IntegerField(default=0)
    text_field = models.CharField(max_length=255, null=True)

    def __str__(self):
        return "Dummy object"


class DummyAuto(cache_model.CacheModel):
    """Dummy model with auto updated fields used for tests"""

    datetime_field = models.DateTimeField(auto_now=True)
    date_field = models.DateField(auto_now=True)
    time_field = models.TimeField(auto_now=True)

    def __str__(self):
        return "Dummy auto object"


class DummyOneToOneCascade(cache_model.CacheModel):
    """Dummy model with related field with cascade on-delete action used for tests"""

    reference = cache_model.OneToOneField(
        Reference, on_delete=cache_model.CASCADE, primary_key=True
    )


class DummyOneToOneDoNothing(cache_model.CacheModel):
    """Dummy model with related field with do-nothing on-delete action used for tests"""

    reference = cache_model.OneToOneField(
        Reference, on_delete=cache_model.DO_NOTHING, primary_key=True
    )


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
        assert Dummy.cache.count() == 0

        dummy_1 = Dummy()
        dummy_1.save()
        dummy_2 = Dummy()
        dummy_2.save()

        assert dummy_1.pk == 1
        assert dummy_1.id == 1
        assert dummy_2.pk == 2
        assert dummy_2.id == 2

        # check object is in cache
        assert Dummy.cache.count() == 2

    def test_delete(self, clear_cache):
        """Test to delete a cache model"""
        assert Dummy.cache.count() == 0

        dummy_1 = Dummy()
        dummy_1.save()
        dummy_2 = Dummy()
        dummy_2.save()
        dummy_1.delete()

        # check object is not in cache
        assert Dummy.cache.count() == 1
        assert Dummy.cache.get(pk=2)

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

    def test_count(self, set_cache, clear_cache):
        """Test to count instances in cache"""
        # assert using store
        dummy_cache = cache.get(Dummy.cache._store_name)
        assert len(dummy_cache) == 3

        # assert using method
        assert Dummy.cache.count() == 3

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

    def test_delete_not_present(self, clear_cache):
        """Test to delete a cache model not saved in cache"""
        dummy = Dummy()
        with pytest.raises(
            ObjectDoesNotExist, match=r"This Dummy does not exist in cache"
        ):
            dummy.delete()


@pytest.mark.django_db(transaction=True)
class TestCacheModelWithRelation:
    def test_one_to_one_cascade_delete(self, clear_cache):
        """Test to delete a related field with a cascade on-delete action"""
        assert DummyOneToOneCascade.cache.count() == 0

        reference = Reference.objects.create()
        dummy = DummyOneToOneCascade.cache.create(reference=reference)

        assert DummyOneToOneCascade.cache.count() == 1
        assert dummy.pk == dummy.reference.pk

        reference.delete()

        assert DummyOneToOneCascade.cache.count() == 0

    def test_one_to_one_cascade_delete_no_instance(self, clear_cache):
        """Test to delete a related field with a cascade on-delete action when
        there are no instance
        """
        assert DummyOneToOneCascade.cache.count() == 0

        reference = Reference.objects.create()

        assert DummyOneToOneCascade.cache.count() == 0

        reference.delete()

        assert DummyOneToOneCascade.cache.count() == 0

    def test_one_to_one_do_nothing_delete(self, clear_cache):
        """Test to delete a related field with a do-nothing on-delete action"""
        assert DummyOneToOneDoNothing.cache.count() == 0

        reference = Reference.objects.create()
        dummy = DummyOneToOneDoNothing.cache.create(reference=reference)

        assert DummyOneToOneDoNothing.cache.count() == 1
        assert dummy.pk == dummy.reference.pk

        reference.delete()

        assert DummyOneToOneDoNothing.cache.count() == 1

    def test_on_delete_not_callable(self, clear_cache):
        """Test to add related field with no callable on-delete action"""
        with pytest.raises(TypeError):

            class DummyInvalid(cache_model.CacheModel):
                """Dummy model with related field used for tests"""

                reference = cache_model.OneToOneField(
                    Reference, on_delete=None, primary_key=True
                )
