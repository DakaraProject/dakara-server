from django.db import models


class SafeDurationField(models.DurationField):
    """ Safe version of DurationField which returns integer to
        the database
    """

    def get_db_prep_value(self, *args, **kwargs):
        value = super(SafeDurationField, self) \
                .get_db_prep_value(*args, **kwargs)
        if value is None:
            return None
        return int(round(value))


class UpperCaseCharField(models.CharField):
    """ Override a Django Model Field and make it upper-case as of Django 1.8
        http://stackoverflow.com/a/33354171
    """

    def __init__(self, *args, **kwargs):
        super(UpperCaseCharField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if value:
            value = value.upper()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(UpperCaseCharField, self).pre_save(model_instance, add)
