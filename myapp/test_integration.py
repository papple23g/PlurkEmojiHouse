# -*- coding: utf-8 -*-
"""
整合測試：實際對真實 Plurk URL 進行爬取
注意：這些測試會實際發送 HTTP 請求到 Plurk API
"""
import sys
from pathlib import Path

import pytest
from django.test import RequestFactory

sys.path.append(str(Path(__file__).parent.parent))  # noqa
from myapp.views import PlurkUrlHtml


@pytest.mark.django_db
@pytest.mark.integration
class TestPlurkUrlHtmlIntegration:
    """整合測試：使用真實 API 測試 PlurkUrlHtml 功能"""
    
    def test_real_plurk_url_3i85k8yyw2(self):
        """
        測試真實噗文：https://www.plurk.com/p/3i85k8yyw2
        
        預期結果：
        1. 大表符（內容）：https://emos.plurk.com/7a659b6e01b51db42b57d0bfaa0df90a_w48_h48.gif
        2. 噗文互動表符：https://emos.plurk.com/f04804af280c6bcb4dd9256ee1a50c8b_w48_h48.png
        3. 留言互動表符：https://emos.plurk.com/12122c248fcdc226b5b8fc65ea47a522_w48_h48.png
        """
        plurk_url = "https://www.plurk.com/p/3i85k8yyw2"
        
        # 建立 request
        factory = RequestFactory()
        request = factory.get('/PlurkUrlHtml/', {'plurk_url': plurk_url})
        
        # 執行實際爬取
        response = PlurkUrlHtml(request)
        html_content = response.content.decode('utf-8')
        
        # 輸出結果以便檢查
        print("\n" + "="*80)
        print("HTML 內容長度:", len(html_content))
        print("="*80)
        
        # 提取所有表符 URL
        import re
        emoji_pattern = r'https://emos\.plurk\.com/[a-zA-Z0-9_]+_w\d+_h\d+\.(png|gif|jpg)'
        emoji_matches = re.findall(emoji_pattern, html_content)
        # findall 會返回完整匹配，但因為有 group，所以需要重新搜尋完整 URL
        all_matches = re.finditer(emoji_pattern, html_content)
        emoji_urls = [match.group(0) for match in all_matches]
        unique_emojis = list(dict.fromkeys(emoji_urls))  # 去重但保持順序
        
        print(f"\n找到 {len(unique_emojis)} 個不重複的表符:")
        for i, emoji_url in enumerate(unique_emojis, 1):
            print(f"{i}. {emoji_url}")
        print("="*80 + "\n")
        
        # 驗證三種關鍵表符
        expected_emojis = {
            "大表符（內容）": "https://emos.plurk.com/7a659b6e01b51db42b57d0bfaa0df90a_w48_h48.gif",
            "噗文互動表符": "https://emos.plurk.com/f04804af280c6bcb4dd9256ee1a50c8b_w48_h48.png",
            "留言互動表符": "https://emos.plurk.com/12122c248fcdc226b5b8fc65ea47a522_w48_h48.png",
        }
        
        for emoji_type, emoji_url in expected_emojis.items():
            assert emoji_url in html_content, f"缺少{emoji_type}: {emoji_url}"
            print(f"✅ 找到{emoji_type}")
        
        # 額外驗證
        assert len(unique_emojis) > 0, "應該至少找到一個表符"
        assert response.status_code == 200, "HTTP 狀態碼應該是 200"
        
        print("\n✅ 所有驗證通過！")
    
    def test_real_plurk_with_different_emojis(self):
        """
        測試其他真實噗文 URL（可以根據需要修改 URL）
        這個測試用於驗證功能在不同噗文上的穩定性
        """
        # 可以替換成其他噗文 URL 進行測試
        plurk_url = "https://www.plurk.com/p/3i85k8yyw2"
        
        factory = RequestFactory()
        request = factory.get('/PlurkUrlHtml/', {'plurk_url': plurk_url})
        
        try:
            response = PlurkUrlHtml(request)
            html_content = response.content.decode('utf-8')
            
            # 基本驗證
            assert response.status_code == 200
            assert len(html_content) > 0
            
            # 檢查是否包含表符 URL
            import re
            emoji_count = len(re.findall(r'https://emos\.plurk\.com/', html_content))
            print(f"\n找到 {emoji_count} 個表符引用")
            
            assert emoji_count > 0, "應該找到至少一個表符"
            
        except Exception as e:
            pytest.fail(f"爬取失敗: {e}")


@pytest.mark.django_db
@pytest.mark.integration
class TestRealApiCalls:
    """測試個別 API 函數的真實調用"""
    
    def test_real_get_reaction_emoji_urls(self):
        """測試真實的噗文互動表符 API"""
        from myapp.views import get_reaction_emoji_urls
        
        # plurk_id for https://www.plurk.com/p/3i85k8yyw2
        plurk_id = 356098869955874
        
        result = get_reaction_emoji_urls(plurk_id)
        
        print(f"\n找到 {len(result)} 個噗文互動表符:")
        for url in result:
            print(f"  - {url}")
        
        # 驗證
        assert isinstance(result, list)
        assert len(result) > 0, "應該至少有一個互動表符"
        
        # 驗證特定的互動表符存在
        expected_url = "https://emos.plurk.com/f04804af280c6bcb4dd9256ee1a50c8b_w48_h48.png"
        assert expected_url in result, f"應該包含 {expected_url}"
    
    def test_real_extract_emoji_from_reactions(self):
        """測試從真實 API 數據提取表符"""
        import certifi
        import requests

        from myapp.views import extract_emoji_urls_from_reactions
        
        plurk_id = 356098869955874
        
        # 實際調用 API
        url = "https://www.plurk.com/v2/reaction/plurk/summary"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)",
            "Content-Type": "application/json",
        }
        data = {"plurk_ids": [plurk_id]}
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10,
            verify=certifi.where(),
        )
        
        api_data = response.json()
        print(f"\nAPI 回應: {api_data}")
        
        # 使用通用函數提取
        emoji_urls = extract_emoji_urls_from_reactions(api_data, data_format='summary')
        
        print(f"\n提取到 {len(emoji_urls)} 個表符 URL:")
        for url in emoji_urls:
            print(f"  - {url}")
        
        assert len(emoji_urls) > 0, "應該提取到至少一個表符"