from http import HTTPStatus
from io import BytesIO
from unittest.mock import Mock, patch

import imagehash
import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from PIL import Image
from taggit.models import Tag, TaggedItem

from myapp.models import CombindEmoji, Emoji, HashOfImage_inputUrl


@pytest.mark.parametrize('path', [
    '/', '/PlurkEmojiHouse', '/PlurkEmojiHouse/', '/ads.txt', '/privacy',
    '/privacy/', '/PlurkEmojiHouse/views', '/PlurkEmojiHouse/search_by_tag',
    '/PlurkEmojiHouse/search_by_url', '/PlurkEmojiHouse/search_by_uuu',
    '/PlurkEmojiHouse/emoji_add_tag', '/PlurkEmojiHouse/delete_tag',
    '/PlurkEmojiHouse/search_tags', '/PlurkEmojiHouse/PlurkUrlHtml',
    '/PlurkEmojiHouse/NumOfEmoji_and_NumOfTag',
    '/PlurkEmojiHouse/numOfEmojiPageBtn', '/PlurkEmojiHouse/emoji_list_add_tag',
    '/PlurkEmojiHouse/AddCombindEmoji', '/PlurkEmojiHouse/SearchCombindEmoji',
    '/PlurkEmojiHouse/DeleteCombindEmoji', '/admin/',
])
def test_existing_routes_resolve(path: str) -> None:
    assert callable(resolve(path).func)


@pytest.mark.django_db
def test_chinese_tags_batch_add_remove_and_search() -> None:
    client = Client()
    emojis = [Emoji.objects.create(url=f'https://emos.plurk.com/test{i}_w48_h48.png') for i in range(2)]
    params = {'emoji_id_str_for_add_list_str': ','.join(str(e.pk) for e in emojis), 'tag_list_str': '貓咪, 可愛'}
    for _ in range(2):
        assert client.get('/PlurkEmojiHouse/emoji_list_add_tag', params).status_code == HTTPStatus.OK
    content_type = ContentType.objects.get_for_model(Emoji)
    assert TaggedItem.objects.filter(content_type=content_type, object_id__in=[e.pk for e in emojis]).count() == 4
    results = client.get('/PlurkEmojiHouse/search_by_tag', {'search_tag': '貓咪,可愛'}).json()
    assert {row['id'] for row in results} == {e.pk for e in emojis}
    assert all(isinstance(row['tags'], str) and {'id', 'url', 'tags', 'imagehash_str'} <= row.keys() for row in results)
    tags, counts = client.get('/PlurkEmojiHouse/search_tags', {'search_tag': '貓'}).json()
    assert tags == ['貓咪'] and counts == [2]
    for emoji in emojis:
        assert client.get('/PlurkEmojiHouse/delete_tag', {'emoji_id': emoji.pk, 'tag_name': '貓咪'}).status_code == HTTPStatus.OK
    assert not Tag.objects.filter(name='貓咪').exists()
    assert all(list(emoji.tags.names()) == ['可愛'] for emoji in emojis)


@pytest.mark.django_db
def test_favorites_are_filtered_for_the_requested_user() -> None:
    client = Client()
    emoji = Emoji.objects.create(url='https://emos.plurk.com/favorite_w48_h48.png')
    assert client.get('/PlurkEmojiHouse/emoji_add_tag', {'id': emoji.pk, 'add_tag_str': '貓咪,__collectorUsers__upgrade_a'}).status_code == HTTPStatus.OK
    own = client.get('/PlurkEmojiHouse/search_by_tag', {'search_tag': '貓咪,__collectorUsers__upgrade_a', 'user_uid': 'upgrade_a'}).json()
    assert own[0]['id'] == emoji.pk
    assert '__be_collected__' in own[0]['tags']
    for user_uid in ('', 'upgrade_b'):
        results = client.get('/PlurkEmojiHouse/search_by_tag', {'search_tag': '貓咪', 'user_uid': user_uid}).json()
        assert '__collectorUsers__' not in results[0]['tags']
        assert '__be_collected__' not in results[0]['tags']
    client.get('/PlurkEmojiHouse/delete_tag', {'emoji_id': emoji.pk, 'tag_name': '__collectorUsers__upgrade_a'})
    assert not emoji.tags.filter(name='__collectorUsers__upgrade_a').exists()


@pytest.mark.django_db
def test_combined_emoji_add_search_and_delete() -> None:
    client = Client()
    urls = ['https://emos.plurk.com/first_w48_h48.png', 'https://emos.plurk.com/second_w48_h48.png']
    combined = '|'.join(urls)
    for _ in range(2):
        assert set(client.get('/PlurkEmojiHouse/AddCombindEmoji', {'combind_url': combined}).json()) == set(urls)
    assert CombindEmoji.objects.filter(combind_url=combined).count() == 1
    for url in urls:
        assert client.get('/PlurkEmojiHouse/SearchCombindEmoji', {'emoji_url': url}).json() == [combined]
    assert client.get('/PlurkEmojiHouse/DeleteCombindEmoji', {'combind_url': combined}).status_code == HTTPStatus.OK
    assert not CombindEmoji.objects.exists()
    assert client.get('/PlurkEmojiHouse/SearchCombindEmoji', {'emoji_url': urls[0]}).json() == []


@pytest.mark.parametrize('image_format', ['PNG', 'GIF', 'JPEG'])
def test_image_hash_matches_the_existing_pillow9_imagehash4_format(image_format: str) -> None:
    image = Image.new('L', (32, 32))
    image.putdata([(x * 13 + y * 7) % 256 for y in range(32) for x in range(32)])
    payload = BytesIO()
    image.save(payload, format=image_format)
    with patch('myapp.models.req.get', return_value=Mock(content=payload.getvalue())):
        computed = HashOfImage_inputUrl('https://emos.plurk.com/hash_fixture.png')
    # Captured using the deployed Pillow 9.5 / ImageHash 4.0 algorithm.
    expected = '39317363e7c6cc8c'
    assert str(computed) == expected
    assert computed - imagehash.hex_to_hash(expected) == 0


@pytest.mark.django_db
def test_saved_hash_search_uses_existing_values_without_downloading() -> None:
    same_hash = '39317363e7c6cc8c'
    emojis = [Emoji.objects.create(url=f'https://emos.plurk.com/hash{i}_w48_h48.png', imagehash_str=same_hash) for i in range(2)]
    with patch('myapp.models.req.get', side_effect=AssertionError('Stored hashes must not be downloaded')):
        results = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': f'__hash__{emojis[0].pk}'}).json()
    assert [row['id'] for row in results] == [emojis[1].pk]


@pytest.mark.django_db
@pytest.mark.parametrize('favorites,combined,expected_indices', [
    (True, False, [3, 1]),
    (False, True, [3, 2]),
    (True, True, [3]),
])
def test_hash_search_accepts_favorite_and_combined_filters(
    favorites: bool, combined: bool, expected_indices: list[int],
) -> None:
    base = Emoji.objects.create(url='https://emos.plurk.com/base.png', imagehash_str='39317363e7c6cc8c')
    candidates = [Emoji.objects.create(url=f'https://emos.plurk.com/filter{i}.png', imagehash_str=base.imagehash_str) for i in range(4)]
    for index in (1, 3):
        candidates[index].tags.add('__collectorUsers__upgrade_a')
    combination = CombindEmoji.objects.create(combind_url='https://emos.plurk.com/combined.png')
    combination.emoji_url_set.add(candidates[2].url, candidates[3].url)
    search_tag = f'__hash__{base.pk}'
    if favorites:
        search_tag += ',__collectorUsers__upgrade_a'
    if combined:
        search_tag += ',__showCombindEmojis__'
    with patch('myapp.models.req.get', side_effect=AssertionError('Stored hashes must not be downloaded')):
        response = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': search_tag, 'user_uid': 'upgrade_a'})
    assert response.status_code == HTTPStatus.OK
    assert [row['id'] for row in response.json()] == [candidates[index].pk for index in expected_indices]


@pytest.mark.django_db
@pytest.mark.parametrize('emoji_id', ['', 'invalid', '-1', '2147483648'])
def test_invalid_hash_search_returns_a_message(emoji_id: str) -> None:
    response = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': f'__hash__{emoji_id}'})
    assert response.status_code == HTTPStatus.OK
    assert response.content.decode() == '沒有該圖片的搜尋結果'


@pytest.mark.django_db
def test_hash_search_threshold_bad_candidates_and_json_privacy() -> None:
    base = Emoji.objects.create(url='https://emos.plurk.com/threshold_base.png', imagehash_str='0000000000000000')
    candidates = [Emoji.objects.create(url=f'https://emos.plurk.com/threshold{i}.png', imagehash_str=value)
                  for i, value in enumerate(('0000000000000000', '000000000000007f', '00000000000000ff', 'broken', '', None))]
    candidates[0].tags.add('貓咪', '__collectorUsers__upgrade_a', '__collectorUsers__upgrade_b')
    with patch('myapp.models.req.get', side_effect=AssertionError('Stored hashes must not be downloaded')):
        response = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': f'__hash__{base.pk}', 'user_uid': 'upgrade_a'})
    assert response.status_code == HTTPStatus.OK
    assert response['Content-Type'] == 'application/json'
    rows = response.json()
    assert [row['id'] for row in rows] == [candidates[1].pk, candidates[0].pk]
    assert set(rows[0]) == {'id', 'url', 'tags', 'imagehash_str'}
    assert '貓咪' in rows[1]['tags'] and '__be_collected__' in rows[1]['tags']
    assert '__collectorUsers__' not in rows[1]['tags']
    anonymous = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': f'__hash__{base.pk}'}).json()
    assert all('__be_collected__' not in row['tags'] for row in anonymous)


@pytest.mark.django_db
@pytest.mark.parametrize('suffix', ['', ',__collectorUsers__nobody', ',__showCombindEmojis__', ',__showCombindEmojis__,__collectorUsers__nobody'])
def test_hash_search_empty_filters_and_pagination(suffix: str) -> None:
    base = Emoji.objects.create(url='https://emos.plurk.com/empty_base.png', imagehash_str='0000000000000000')
    search_tag = f'__hash__{base.pk}{suffix}'
    assert Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': search_tag}).json() == []
    pages = Client().get('/PlurkEmojiHouse/numOfEmojiPageBtn', {'search_tag': search_tag})
    assert pages.status_code == HTTPStatus.OK and pages.content == b'1'


@pytest.mark.django_db
def test_hash_search_missing_source() -> None:
    response = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': '__hash__61935,__collectorUsers__upgrade_a'})
    assert response.status_code == HTTPStatus.OK
    assert response.content.decode() == '沒有該圖片的搜尋結果'


@pytest.mark.django_db
def test_hash_search_calculates_source_once_and_preserves_candidates() -> None:
    image = Image.new('L', (32, 32))
    image.putdata([(x * 13 + y * 7) % 256 for y in range(32) for x in range(32)])
    payload = BytesIO()
    image.save(payload, format='PNG')
    base = Emoji.objects.create(url='https://emos.plurk.com/uncached_source.png')
    candidate = Emoji.objects.create(url='https://emos.plurk.com/cached_candidate.png', imagehash_str='39317363e7c6cc8c')
    uncached_candidate = Emoji.objects.create(url='https://emos.plurk.com/uncached_candidate.png')
    with patch('myapp.models.req.get', return_value=Mock(content=payload.getvalue())) as download:
        for _ in range(2):
            rows = Client().get('/PlurkEmojiHouse/search_by_tag', {'search_tag': f'__hash__{base.pk}'}).json()
            assert [row['id'] for row in rows] == [candidate.pk]
    download.assert_called_once()
    assert download.call_args.args == (base.url,)
    base.refresh_from_db()
    candidate.refresh_from_db()
    uncached_candidate.refresh_from_db()
    assert base.imagehash_str == candidate.imagehash_str == '39317363e7c6cc8c'
    assert uncached_candidate.imagehash_str is None


@pytest.mark.django_db
@pytest.mark.parametrize('user_uid', [None, 'upgrade_a'])
def test_search_does_not_query_tags_for_each_emoji(user_uid: str | None) -> None:
    for index in range(20):
        emoji = Emoji.objects.create(url=f'https://emos.plurk.com/prefetch{index}_w48_h48.png')
        emoji.tags.add('貓咪')
    ContentType.objects.clear_cache()
    params = {'search_tag': ''}
    if user_uid:
        params['user_uid'] = user_uid
    with CaptureQueriesContext(connection) as queries:
        results = Client().get('/PlurkEmojiHouse/search_by_tag', params).json()
    assert len(results) == 20
    assert len(queries) <= 3, 'Tag queries must stay bounded when the result page grows'
