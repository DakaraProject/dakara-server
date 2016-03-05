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
