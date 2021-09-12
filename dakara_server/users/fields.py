from django.db import models


class CaseInsensitiveFieldMixin:
    """Field mixin that uses case-insensitive lookup alternatives if they exist.

    See: https://concisecoder.io/2018/10/27/case-insensitive-fields-in-django-models/
    """

    LOOKUP_CONVERSIONS = {
        "exact": "iexact",
        "contains": "icontains",
        "startswith": "istartswith",
        "endswith": "iendswith",
        "regex": "iregex",
    }

    def get_lookup(self, lookup_name):
        converted = self.LOOKUP_CONVERSIONS.get(lookup_name, lookup_name)
        return super().get_lookup(converted)


class CaseInsensitiveCharField(CaseInsensitiveFieldMixin, models.CharField):
    """Case insensitive char field."""


class CaseInsensitiveEmailField(CaseInsensitiveFieldMixin, models.EmailField):
    """Case insensitive email field."""
