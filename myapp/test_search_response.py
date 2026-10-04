import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from django.test import Client

from myapp.models import CombindEmoji, Emoji


@pytest.fixture
def browser_search() -> dict[str, Any]:
    # Execute the actual Brython request function, with only browser/DOM boundaries mocked.
    source = Path(__file__).resolve().parents[1] / 'templates' / 'request_function.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'SendRequest_searchEmoji')
    doc = {name: MagicMock() for name in (
        'div_fa_list', 'search_tag', 'search_tag_result', 'emoji_result_table', 'emoji_page_btns',
        'checkbox_showCollectEmojis', 'checkbox_showCombindEmojis',
    )}
    doc['emoji_result_table'].__le__.return_value = True
    doc['div_fa_list'].classList = ['on_pressed']
    doc['search_tag'].value = '__hash__61935'
    doc['checkbox_showCollectEmojis'].checked = False
    doc['checkbox_showCombindEmojis'].checked = False
    auth = Mock(return_value=SimpleNamespace(currentUser=None))
    request = MagicMock()
    namespace = {
        'doc': doc, 'window': SimpleNamespace(firebase=SimpleNamespace(auth=auth)),
        'ajax': SimpleNamespace(ajax=Mock(return_value=request)), 'json': json,
        '_pg': {'total': 1, 'before_id_for_page': {}}, 'P': Mock(side_effect=str),
        'TABLE_emojiReslut': Mock(return_value='table'), 'DIV_emojiReslut_Block': Mock(return_value='grid'),
        '_build_pagination': Mock(), 'SendRequest_insertEmojiPageBtn': Mock(), 'SendRequest_searchTags': Mock(),
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
    namespace['request'] = request
    namespace['auth'] = auth
    namespace['event'] = SimpleNamespace(currentTarget=SimpleNamespace(id='search_tag_btn'))
    return namespace


@pytest.mark.parametrize('uid,favorites,combined,suffix', [
    (None, False, False, ''),
    (None, True, False, ''),
    ('upgrade_a', True, False, ',__collectorUsers__upgrade_a'),
    ('upgrade_a', False, True, ',__showCombindEmojis__'),
    ('upgrade_a', True, True, ',__collectorUsers__upgrade_a,__showCombindEmojis__'),
])
def test_browser_search_builds_hash_and_filter_request(
    browser_search: dict[str, Any], uid: str | None, favorites: bool, combined: bool, suffix: str,
) -> None:
    state = browser_search
    state['auth'].return_value.currentUser = SimpleNamespace(uid=uid) if uid else None
    state['doc']['checkbox_showCollectEmojis'].checked = favorites
    state['doc']['checkbox_showCombindEmojis'].checked = combined
    state['SendRequest_searchEmoji'](state['event'])
    state['request'].open.assert_called_once_with(
        'GET', f'/PlurkEmojiHouse/search_by_tag?search_tag=__hash__61935{suffix}&page=0&user_uid={uid}&num_of_emoji_per_page=20', True,
    )
    state['request'].send.assert_called_once()
    state['request'].set_timeout.assert_called_once()
    state['SendRequest_insertEmojiPageBtn'].assert_called_once_with('__hash__61935' + suffix, 20)


@pytest.mark.parametrize('status,text,expected', [
    (500, '<html>error</html>', '搜尋失敗，請稍後再試'),
    (0, '', '搜尋失敗，請稍後再試'),
    (200, '', '搜尋失敗，請稍後再試'),
    (200, '<html>not JSON</html>', '搜尋失敗，請稍後再試'),
    (200, '{}', '搜尋失敗，請稍後再試'),
    (200, 'null', '搜尋失敗，請稍後再試'),
    (200, '[{"id": "invalid"}]', '搜尋失敗，請稍後再試'),
    (200, '[]', '沒有符合條件的表符'),
    (200, '沒有該圖片的搜尋結果', '沒有該圖片的搜尋結果'),
])
def test_browser_search_displays_empty_and_failed_responses(
    browser_search: dict[str, Any], status: int, text: str, expected: str,
) -> None:
    state = browser_search
    state['SendRequest_searchEmoji'](state['event'])
    callbacks = dict(call.args for call in state['request'].bind.call_args_list)
    callbacks['complete'](SimpleNamespace(status=status, text=text))
    state['P'].assert_called_once_with(expected)
    state['doc']['emoji_result_table'].__le__.assert_called_once_with(expected)
    state['doc']['emoji_page_btns'].clear.assert_called_once()
    state['TABLE_emojiReslut'].assert_not_called()
    state['DIV_emojiReslut_Block'].assert_not_called()


@pytest.mark.parametrize('combined', [False, True])
def test_browser_search_filtered_empty_response_explains_filters(browser_search: dict[str, Any], combined: bool) -> None:
    state = browser_search
    state['auth'].return_value.currentUser = SimpleNamespace(uid='upgrade_a')
    state['doc']['checkbox_showCollectEmojis'].checked = not combined
    state['doc']['checkbox_showCombindEmojis'].checked = combined
    state['SendRequest_searchEmoji'](state['event'])
    callbacks = dict(call.args for call in state['request'].bind.call_args_list)
    callbacks['complete'](SimpleNamespace(status=200, text='[]'))
    state['P'].assert_called_once_with('沒有符合條件的表符，可取消「顯示我的收藏」或「組合表符」再試')


@pytest.mark.parametrize('list_view', [False, True])
def test_browser_search_renders_results_and_records_cursor(browser_search: dict[str, Any], list_view: bool) -> None:
    state = browser_search
    state['doc']['div_fa_list'].classList = ['on_pressed'] if list_view else []
    state['_pg']['total'] = 3
    state['SendRequest_searchEmoji'](state['event'])
    callbacks = dict(call.args for call in state['request'].bind.call_args_list)
    response = SimpleNamespace(status=200, text='[{"id": 99}, {"id": 42}]')
    callbacks['complete'](response)
    renderer = state['TABLE_emojiReslut'] if list_view else state['DIV_emojiReslut_Block']
    renderer.assert_called_once_with(response)
    state['doc']['emoji_result_table'].__le__.assert_called_once_with('table' if list_view else 'grid')
    assert state['_pg']['before_id_for_page'] == {2: 42}
    state['_build_pagination'].assert_called_once_with(1)
    state['P'].assert_not_called()


def test_browser_search_timeout_clears_stale_results_and_pages(browser_search: dict[str, Any]) -> None:
    state = browser_search
    state['SendRequest_searchEmoji'](state['event'])
    timeout = state['request'].set_timeout.call_args.args[1]
    timeout(SimpleNamespace())
    state['doc']['emoji_result_table'].clear.assert_called_once()
    state['doc']['emoji_page_btns'].clear.assert_called_once()
    state['P'].assert_called_once_with('搜尋逾時，請重新整理頁面後再試一次')


@pytest.mark.parametrize('event', ['complete', 'loading', 'timeout'])
def test_browser_search_ignores_stale_callbacks(browser_search: dict[str, Any], event: str) -> None:
    state = browser_search
    state['SendRequest_searchEmoji'](state['event'])
    callbacks = dict(call.args for call in state['request'].bind.call_args_list)
    stale = state['request'].set_timeout.call_args.args[1] if event == 'timeout' else callbacks[event]
    current_request = MagicMock()
    state['ajax'].ajax.return_value = current_request
    state['doc']['search_tag'].value = '__hash__61935,__collectorUsers__upgrade_a'
    state['SendRequest_searchEmoji'](state['event'])
    stale(SimpleNamespace(status=200, text='[{"id": 42}]'))
    state['doc']['emoji_result_table'].clear.assert_not_called()
    state['P'].assert_not_called()
    state['TABLE_emojiReslut'].assert_not_called()
    current_callbacks = dict(call.args for call in current_request.bind.call_args_list)
    current_callbacks['complete'](SimpleNamespace(status=200, text='[]'))
    state['P'].assert_called_once_with('沒有符合條件的表符，可取消「顯示我的收藏」或「組合表符」再試')


@pytest.mark.django_db
@pytest.mark.parametrize('favorites,combined,expected_count', [(False, False, 2), (True, False, 1), (False, True, 1), (True, True, 1)])
def test_browser_request_database_and_response_rendering_integration(
    browser_search: dict[str, Any], favorites: bool, combined: bool, expected_count: int,
) -> None:
    state = browser_search
    base = Emoji.objects.create(pk=61935, url='https://emos.plurk.com/pipeline_base.png', imagehash_str='39317363e7c6cc8c')
    candidates = [Emoji.objects.create(url=f'https://emos.plurk.com/pipeline{i}.png', imagehash_str=base.imagehash_str) for i in range(2)]
    candidates[1].tags.add('__collectorUsers__upgrade_a')
    combination = CombindEmoji.objects.create(combind_url=candidates[1].url)
    combination.emoji_url_set.add(candidates[1].url)
    state['auth'].return_value.currentUser = SimpleNamespace(uid='upgrade_a')
    state['doc']['checkbox_showCollectEmojis'].checked = favorites
    state['doc']['checkbox_showCombindEmojis'].checked = combined
    state['SendRequest_searchEmoji'](state['event'])
    request_url = state['request'].open.call_args.args[1]
    response = Client().get(request_url)
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == expected_count and rows[0]['id'] == candidates[1].pk
    callbacks = dict(call.args for call in state['request'].bind.call_args_list)
    browser_response = SimpleNamespace(status=response.status_code, text=response.content.decode())
    callbacks['complete'](browser_response)
    state['TABLE_emojiReslut'].assert_called_once_with(browser_response)
    state['P'].assert_not_called()
    assert Client().get('/PlurkEmojiHouse/numOfEmojiPageBtn', {'search_tag': f'__hash__{base.pk}'}).content == b'1'
