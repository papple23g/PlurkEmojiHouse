from concurrent.futures import ThreadPoolExecutor
import datetime
from http import HTTPStatus
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, close_old_connections, connection
from django.test import Client
from django.utils import timezone

from myapp.models import SiteViews


def test_postgresql_timezone_compatibility() -> None:
    from mysite2.postgresql.base import utc_tzinfo_factory

    assert utc_tzinfo_factory(0) == datetime.timezone.utc
    assert utc_tzinfo_factory(datetime.timedelta(0)) == datetime.timezone.utc
    with pytest.raises(AssertionError):
        utc_tzinfo_factory(datetime.timedelta(hours=8))


@pytest.mark.django_db
def test_counter_requires_csrf_and_cannot_overwrite_total() -> None:
    counter = SiteViews.objects.create(
        name="PlurkEmojiHouse", total=123, imported_total=123, imported_at=timezone.now()
    )
    client = Client(enforce_csrf_checks=True)
    assert client.get('/PlurkEmojiHouse/views').status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert client.post('/PlurkEmojiHouse/views').status_code == HTTPStatus.FORBIDDEN
    page = client.get('/PlurkEmojiHouse')
    assert page.status_code == HTTPStatus.OK
    assert b'site_view_csrf' in page.content
    assert b'G-W2NEV5695P' in page.content
    assert b'UA-135785524-1' not in page.content
    assert client.get('/ads.txt').content.decode().strip() == 'google.com, pub-3626951597834728, DIRECT, f08c47fec0942fa0'
    assert client.get('/privacy').status_code == HTTPStatus.OK
    response = client.post(
        '/PlurkEmojiHouse/views', {'total': 0}, HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value
    )
    assert response.json() == {'total': 124}
    counter.refresh_from_db()
    assert counter.total == 124
    assert counter.imported_total == 123
    assert client.get('/admin/myapp/siteviews/').status_code == HTTPStatus.FOUND


@pytest.mark.django_db
def test_uninitialized_counter_does_not_start_at_zero() -> None:
    assert Client().post('/PlurkEmojiHouse/views').status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert not SiteViews.objects.exists()


@pytest.mark.django_db
def test_counter_failure_does_not_break_page() -> None:
    with patch('myapp.views.SiteViews.objects.filter', side_effect=DatabaseError):
        assert Client().post('/PlurkEmojiHouse/views').status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert Client().get('/PlurkEmojiHouse').status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_admin_counter_is_read_only() -> None:
    from django.contrib.auth import get_user_model

    SiteViews.objects.create(
        name='PlurkEmojiHouse', total=100, imported_total=100, imported_at=timezone.now()
    )
    user = get_user_model().objects.create(username='counter-test', is_staff=True, is_superuser=True)
    client = Client()
    client.force_login(user)
    response = client.get('/admin/myapp/siteviews/PlurkEmojiHouse/change/')
    assert response.status_code == HTTPStatus.OK
    assert b'name="total"' not in response.content
    client.post('/admin/myapp/siteviews/PlurkEmojiHouse/change/', {'total': 0, '_save': 'Save'})
    assert SiteViews.objects.get().total == 100
    assert client.get('/admin/myapp/siteviews/add/').status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_import_is_validated_and_never_overwrites() -> None:
    response = Mock()
    with patch('myapp.management.commands.import_site_views.requests.get', return_value=response) as get:
        response.json.return_value = None
        with pytest.raises(CommandError):
            call_command('import_site_views', stdout=StringIO())
        assert not SiteViews.objects.exists()
        response.json.return_value = 126904
        call_command('import_site_views', stdout=StringIO())
        counter = SiteViews.objects.get()
        assert counter.total == counter.imported_total == 126904
        assert counter.imported_at is not None
        get.reset_mock()
        response.json.return_value = 0
        call_command('import_site_views', stdout=StringIO())
        get.assert_not_called()
        assert SiteViews.objects.get().total == 126904


@pytest.mark.django_db(transaction=True)
def test_concurrent_page_views() -> None:
    if connection.vendor != 'postgresql':
        pytest.skip('Production concurrency check requires PostgreSQL')
    SiteViews.objects.create(
        name='PlurkEmojiHouse', total=100, imported_total=100, imported_at=timezone.now()
    )

    def visit(_: int) -> int:
        close_old_connections()
        try:
            return Client().post('/PlurkEmojiHouse/views').status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(visit, range(32)))
    assert statuses == [HTTPStatus.OK] * 32
    assert SiteViews.objects.get().total == 132
