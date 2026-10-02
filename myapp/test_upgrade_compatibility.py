from http import HTTPStatus
from io import BytesIO
from unittest.mock import Mock, patch

import imagehash
import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import Client
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
