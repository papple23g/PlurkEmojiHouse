from pathlib import Path
import ast
import re
from html import unescape

import pytest
from django.test import Client


@pytest.mark.django_db
def test_shared_articles_and_fallback_navigation() -> None:
    client = Client()
    home = client.get('/').content.decode()
    root = Path(__file__).resolve().parents[1]
    for name in ('guide', 'privacy'):
        article = (root / 'templates' / f'{name}_content.html').read_text(encoding='utf-8')
        standalone = client.get(f'/{name}').content.decode()
        assert article in home and article in standalone
        assert standalone.count('← 返回表符搜尋') == 2
        assert '<script' not in article and '<iframe' not in article
    assert 'aria-labelledby="plurk-help-title"' in home
    assert 'data-dialog-content="quick"' not in home
    assert home.count('data-dialog-content="guide"') == 1
    sidebar = home.split('<nav class="publisher_links"')[1].split('</nav>')[0]
    assert '/guide' not in sidebar
    guide = (root / 'templates' / 'guide_content.html').read_text(encoding='utf-8')
    assert '<span class="guide-tag">開心</span>' in guide
    assert '<span class="guide-tag">貓</span>' in guide
    assert 'onclick=' not in guide
    assert '<img' not in guide and '<figure' not in guide
    assert '/static/guide/' not in home
    assert guide.count('<li>') == 5
    assert guide.count('<svg ') == 3
    assert '<button' not in guide and 'tabindex' not in guide
    assert '示意元件不會執行操作。' not in guide
    standalone = client.get('/guide').content.decode().split('<body>')[1].split('</body>')[0]
    standalone_text = re.sub(r'\s', '', unescape(re.sub(r'<[^>]*>', '', standalone)))
    dialog_text = re.sub(r'\s', '', unescape(re.sub(r'<[^>]*>', '', guide))) + '使用說明×關閉，回到搜尋'
    assert len(standalone_text) <= 200
    assert len(dialog_text) <= 200
    privacy = client.get('/privacy').content.decode()
    assert 'Firebase Authentication' not in privacy
    assert '帳戶識別碼' not in privacy
    assert '其他廣告供應商' in privacy and '其他網站' in privacy
    assert 'Cookie' in privacy and 'myadcenter.google.com' in privacy
    assert 'aboutads.info/choices/' in privacy


@pytest.mark.django_db
def test_standalone_author_links_point_to_the_existing_author_information() -> None:
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / 'templates/PlurkEmojiPage.py').read_text(encoding='utf-8'))
    author = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == 'DIV_about_author')
    author_url = next(keyword.value.value for node in ast.walk(author) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Name) and node.func.id == 'IFRAME'
                      for keyword in node.keywords if keyword.arg == 'src')
    assert author_url.startswith('https://hackmd.io/')
    client = Client()
    for path in ('/guide', '/privacy', '/PlurkEmojiHouse'):
        content = client.get(path).content.decode()
        links = re.findall(r'<a href="([^"]+)" data-author-link>', content)
        assert links and all(link == author_url for link in links)
