import datetime

from django.conf import settings
from django.db.backends.postgresql.base import DatabaseWrapper as PostgreSQLWrapper
from psycopg2.extensions import cursor as Cursor


def utc_tzinfo_factory(offset: int | datetime.timedelta) -> datetime.tzinfo:
    # Django #32856: psycopg2 2.9 changed minutes (int) to timedelta.
    if offset not in (0, datetime.timedelta(0)):
        raise AssertionError("database connection isn't set to UTC")
    return datetime.timezone.utc


class DatabaseWrapper(PostgreSQLWrapper):
    # ponytail: compatibility shim for Django 2.2; remove after upgrading Django.
    def create_cursor(self, name: str | None = None) -> Cursor:
        cursor = super().create_cursor(name)
        if settings.USE_TZ:
            cursor.tzinfo_factory = utc_tzinfo_factory
        return cursor
