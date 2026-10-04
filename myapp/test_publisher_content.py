import ast
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.db import DatabaseError
from django.test import Client

from myapp.models import Emoji


@pytest.mark.django_db
def test_initial_content_and_advertising_boundaries() -> None:
    client = Client()
    for _ in range(21):
        emoji = Emoji.objects.create(url='https://emos.plurk.com/example.png')
        emoji.tags.add('開心', '<script>private</script>', '__collectorUsers__private-uid')
    for path in ('/', '/PlurkEmojiHouse', '/PlurkEmojiHouse/'):
        content = client.get(path).content.decode()
        # Initial content must be in HTML outside the Brython script.
        initial_content = content.split('<script type="text/python">')[0]
        assert '<h1' in initial_content and '用標籤找表符，點擊圖片即可複製。' in initial_content
        assert initial_content.count('class="initial_emoji"') == 20
        assert '<table aria-label="最近收錄的表符清單">' in initial_content
        assert '開心' in initial_content and '&lt;script&gt;private&lt;/script&gt;' in initial_content
        assert '__collectorUsers__' not in initial_content and 'private-uid' not in initial_content
        assert 'pagead2.googlesyndication.com' not in content
        assert 'google-adsense-account' in content and 'G-W2NEV5695P' in content
        assert 'id="plurk-ad-preview"' not in content
    guide = client.get('/guide').content.decode()
    assert guide.count('pagead2.googlesyndication.com') == 1
    assert '<h1>使用說明</h1>' in guide
    assert 'brython' not in guide and 'firebase' not in guide
    assert 'pagead2.googlesyndication.com' not in client.get('/privacy').content.decode()
    assert 'pagead2.googlesyndication.com' not in client.get('/admin/login/').content.decode()
    with patch('myapp.views.Emoji.objects.prefetch_related', side_effect=DatabaseError):
        response = client.get('/')
        assert response.status_code == 200
        assert '目前無法顯示最近收錄的表符' in response.content.decode()
        assert '使用說明' in response.content.decode()
    Emoji.objects.all().delete()
    assert '目前無法顯示最近收錄的表符' in client.get('/').content.decode()


def test_search_callbacks_preserve_loading_content_and_ignore_stale_results() -> None:
    # Execute the real Brython callback with minimal DOM stand-ins; no browser or network needed.
    source = Path(__file__).resolve().parents[1] / 'templates' / 'request_function.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    callbacks = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                 and node.name in ('OnComplete_searchEmoji', 'OnLoading_searchEmoji',
                                   'Timeout_searchEmoji', 'OnComplete_insertEmojiPageBtn')]

    class Element:
        def __init__(self) -> None:
            self.content: list[str] = []
            self.style = SimpleNamespace(display='block')
            self.classList = ['on_pressed']

        def clear(self) -> None:
            self.content.clear()

        def __le__(self, content: str) -> bool:
            self.content.append(content)
            return True

    doc = {key: Element() for key in ('emoji_result_table', 'emoji_page_btns', 'div_fa_list', 'initial_gallery')}
    table, grid = Mock(return_value='table'), Mock(return_value='grid')
    sidebar = SimpleNamespace(setSearchState=Mock())
    namespace = {'doc': doc, 'json': json, 'P': str, '_pg': {'pending_page': 0},
                 'window': SimpleNamespace(plurkSidebar=sidebar),
                 'request_sequence': 1, '_search_request_sequence': 1,
                 'search_tag_str': '開心', 'num_of_emoji_per_page': 20,
                 'TABLE_emojiReslut': table, 'DIV_emojiReslut_Block': grid,
                 'request_type': '', '_build_pagination': Mock()}
    exec(compile(ast.Module(body=callbacks, type_ignores=[]), str(source), 'exec'), namespace)
    complete = namespace['OnComplete_searchEmoji']
    doc['emoji_result_table'].content = ['previous results']
    namespace['OnLoading_searchEmoji'](SimpleNamespace())
    assert doc['emoji_result_table'].content == ['previous results']
    sidebar.setSearchState.assert_called_with('loading')
    valid = json.dumps([{'id': 9, 'url': 'https://emos.plurk.com/example.png', 'tags': '開心'}])
    for status, text, message in (
        (500, valid, '搜尋失敗'), (200, '', '搜尋失敗'),
        (200, '<html>failure</html>', '格式錯誤'), (200, '{}', '格式錯誤'),
        (200, '[{"id": 1}]', '格式錯誤'), (200, '[]', '沒有符合'),
        (200, '沒有符合 測試 的搜尋結果', '沒有符合'),
    ):
        complete(SimpleNamespace(status=status, text=text))
        assert message in doc['emoji_result_table'].content[0]
        assert doc['initial_gallery'].style.display == 'none'
        table.assert_not_called()
        grid.assert_not_called()
    complete(SimpleNamespace(status=200, text=valid))
    assert doc['emoji_result_table'].content == ['table']
    assert doc['initial_gallery'].style.display == 'none'
    assert namespace['_pg']['before_id_for_page'] == {2: 9}
    sidebar.setSearchState.assert_called_with('ready')
    doc['div_fa_list'].classList.clear()
    complete(SimpleNamespace(status=200, text=valid))
    assert doc['emoji_result_table'].content == ['grid']
    namespace['_search_request_sequence'] = 2
    for name in ('OnComplete_searchEmoji', 'OnLoading_searchEmoji',
                 'Timeout_searchEmoji', 'OnComplete_insertEmojiPageBtn'):
        namespace[name](SimpleNamespace(status=500, text='stale'))
    assert doc['emoji_result_table'].content == ['grid']
    namespace['_search_request_sequence'] = 1
    namespace['Timeout_searchEmoji'](SimpleNamespace())
    assert '搜尋逾時' in doc['emoji_result_table'].content[0]
    sidebar.setSearchState.assert_called_with('error')
    namespace['OnComplete_insertEmojiPageBtn'](SimpleNamespace(status=200, text='9'))
    assert doc['emoji_page_btns'].content == []
    namespace['_pg']['failed_sequence'] = None
    namespace['_pg']['results_ready'] = False
    pagination = namespace['_build_pagination']
    pagination.reset_mock()
    namespace['OnComplete_insertEmojiPageBtn'](SimpleNamespace(status=200, text='3'))
    pagination.assert_not_called()
    complete(SimpleNamespace(status=200, text=valid))
    pagination.assert_called_once_with(1)


@pytest.mark.django_db
def test_preview_is_loopback_only(settings: object) -> None:
    settings.PLURK_LAYOUT_PREVIEW = True
    client = Client()
    assert 'id="plurk-ad-preview"' not in client.get('/?preview_layout=b').content.decode()
    content = client.get('/?preview_layout=b', HTTP_HOST='127.0.0.1:8775').content.decode()
    assert 'id="plurk-ad-preview"' in content and 'data-variant="b"' in content
    assert 'data-variant="a"' in client.get('/?preview_layout=invalid', HTTP_HOST='localhost').content.decode()
