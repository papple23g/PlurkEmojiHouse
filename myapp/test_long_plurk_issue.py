# -*- coding: utf-8 -*-
import pytest
from django.test import RequestFactory
import sys
from pathlib import Path

# 加入專案路徑
sys.path.append(str(Path(__file__).parent.parent))
from myapp.views import PlurkUrlHtml

@pytest.mark.django_db
def test_long_plurk_emoji_retrieval():
    """
    測試長噗文是否能抓到後半部的表符
    噗文：https://www.plurk.com/p/3i808b52m7
    目標表符：https://emos.plurk.com/bc39579430cf52ac0a47fda42af7862c_w48_h48.gif
    """
    plurk_url = "https://www.plurk.com/p/3i808b52m7"
    target_emoji = "https://emos.plurk.com/bc39579430cf52ac0a47fda42af7862c_w48_h48.gif"
    
    factory = RequestFactory()
    request = factory.get('/PlurkUrlHtml/', {'plurk_url': plurk_url})
    
    response = PlurkUrlHtml(request)
    assert response.status_code == 200
    
    html_content = response.content.decode('utf-8')
    
    # 驗證是否包含目標表符
    assert target_emoji in html_content, f"未能從長噗文中獲取表符: {target_emoji}"
    print(f"成功獲取表符: {target_emoji}")
