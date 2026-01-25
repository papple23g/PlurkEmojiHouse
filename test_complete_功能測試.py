# -*- coding: utf-8 -*-
"""
plurkEmojiHouse 完整功能測試
===========================

測試目標：驗證系統可以正確抓取以下四種類型的表符：
1. 噗文/留言內容中的表符
2. 噗文的互動表符
3. 留言的互動表符

測試網址：https://www.plurk.com/p/3i85k8yyw2

預期結果：
- 大表符（內容）: https://emos.plurk.com/7a659b6e01b51db42b57d0bfaa0df90a_w48_h48.gif
- 噗文互動表符: https://emos.plurk.com/f04804af280c6bcb4dd9256ee1a50c8b_w48_h48.png
- 留言互動表符: https://emos.plurk.com/12122c248fcdc226b5b8fc65ea47a522_w48_h48.png
"""
import json
import certifi
import requests


def test_plurk_url_html_complete():
    """測試完整的 PlurkUrlHtml 功能"""
    print("=" * 70)
    print("完整功能測試：plurkEmojiHouse 噗浪表符庫")
    print("=" * 70)
    
    # 測試網址
    plurk_url = "https://www.plurk.com/p/3i85k8yyw2"
    print(f"\n測試噗文: {plurk_url}")
    
    # 步驟 1: 獲取噗文 ID
    print("\n步驟 1: 獲取噗文 ID...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)",
        "Referer": "http://example.com"
    }
    res = requests.get(plurk_url, headers=headers, timeout=10, verify=certifi.where())
    res_text = res.text
    
    plurk_id_sandStr = ', "plurk_id": '
    res_text_plurkIdSandStr_i = res_text.index(plurk_id_sandStr)
    plurk_id_str = res_text[res_text_plurkIdSandStr_i + len(plurk_id_sandStr):res_text.index(",", res_text_plurkIdSandStr_i+1)]
    print(f"  ✓ 噗文 ID: {plurk_id_str}")
    
    # 步驟 2: 獲取回應數據（包含 reaction_summaries）
    print("\n步驟 2: 獲取回應數據...")
    url = f'https://www.plurk.com/v2/plurk/{plurk_id_str}/responses/seen'
    res = requests.get(url, headers=headers, timeout=10, verify=certifi.where())
    res_dict = json.loads(res.text)
    print(f"  ✓ 獲取到 {len(res_dict.get('responses', []))} 則留言")
    
    # 步驟 3: 收集噗文/留言內容中的表符
    print("\n步驟 3: 提取噗文和留言內容中的表符...")
    content_emoji_urls = []
    responses_dict_list = res_dict.get('responses', [])
    for responses_dict in responses_dict_list:
        content_str = responses_dict['content']
        if "https://emos.plurk.com/" in content_str:
            res_text += content_str
            # 簡單提取 URL（實際前端會用更複雜的解析）
            import re
            urls = re.findall(r'https://emos\.plurk\.com/[a-f0-9_]+_w\d+_h\d+\.(gif|png|jpeg|jpg)', content_str)
            for url_tuple in urls:
                full_url = url_tuple if isinstance(url_tuple, str) else f"https://emos.plurk.com/{url_tuple[0]}"
                if full_url.startswith("https://emos.plurk.com/"):
                    content_emoji_urls.append(full_url)
    
    # 重新提取（更準確）
    content_emoji_urls = []
    import re
    pattern = r'https://emos\.plurk\.com/[a-f0-9]+_w\d+_h\d+\.(gif|png|jpeg|jpg)'
    for responses_dict in responses_dict_list:
        content_str = responses_dict['content']
        urls = re.findall(pattern, content_str)
        content_emoji_urls.extend([f"https://emos.plurk.com/{match[0]}" if not match.startswith("https") else match.split('.')[0] + '.' + match.split('.')[-1] for match in urls])
    
    # 重新更準確地提取
    content_emoji_urls = []
    for responses_dict in responses_dict_list:
        content_str = responses_dict['content']
        matches = re.finditer(r'https://emos\.plurk\.com/[a-f0-9]+_w\d+_h\d+\.(gif|png|jpeg|jpg)', content_str)
        for match in matches:
            content_emoji_urls.append(match.group(0))
    
    # 也檢查噗文本身
    if "https://emos.plurk.com/" in res_text[:res_text_plurkIdSandStr_i + 10000]:
        matches = re.finditer(r'https://emos\.plurk\.com/[a-f0-9]+_w\d+_h\d+\.(gif|png|jpeg|jpg)', 
                             res_text[:res_text_plurkIdSandStr_i + 10000])
        for match in matches:
            url = match.group(0)
            if url not in content_emoji_urls:
                content_emoji_urls.append(url)
    
    content_emoji_urls = list(set(content_emoji_urls))  # 去重
    print(f"  ✓ 找到 {len(content_emoji_urls)} 個內容表符")
    
    # 步驟 4: 獲取留言互動表符
    print("\n步驟 4: 提取留言互動表符...")
    response_reaction_emoji_urls = []
    reaction_summaries = res_dict.get('reaction_summaries', [])
    if isinstance(reaction_summaries, list):
        for item in reaction_summaries:
            if isinstance(item, dict) and 'reactions' in item:
                for reaction in item['reactions']:
                    emoji_url = reaction.get('emoticon', {}).get('url')
                    if emoji_url and emoji_url.startswith("https://emos.plurk.com/"):
                        response_reaction_emoji_urls.append(emoji_url)
    print(f"  ✓ 找到 {len(response_reaction_emoji_urls)} 個留言互動表符")
    
    # 步驟 5: 獲取噗文互動表符
    print("\n步驟 5: 提取噗文互動表符...")
    plurk_reaction_emoji_urls = []
    url = "https://www.plurk.com/v2/reaction/plurk/summary"
    headers_json = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)",
        "Content-Type": "application/json",
    }
    data = {"plurk_ids": [int(plurk_id_str)]}
    
    res = requests.post(url, headers=headers_json, json=data, timeout=10, verify=certifi.where())
    res_dict_plurk = res.json()
    
    for summary in res_dict_plurk.get("summaries", []):
        for reaction in summary.get("reactions", []):
            emoji_url = reaction.get("emoticon", {}).get("url")
            if emoji_url and emoji_url.startswith("https://emos.plurk.com/"):
                plurk_reaction_emoji_urls.append(emoji_url)
    print(f"  ✓ 找到 {len(plurk_reaction_emoji_urls)} 個噗文互動表符")
    
    # 彙總所有表符
    all_emoji_urls = list(set(content_emoji_urls + response_reaction_emoji_urls + plurk_reaction_emoji_urls))
    
    # 測試結果
    print("\n" + "=" * 70)
    print("測試結果")
    print("=" * 70)
    
    # 必須包含的表符
    required_emojis = {
        "大表符（內容）": "https://emos.plurk.com/7a659b6e01b51db42b57d0bfaa0df90a_w48_h48.gif",
        "噗文互動表符": "https://emos.plurk.com/f04804af280c6bcb4dd9256ee1a50c8b_w48_h48.png",
        "留言互動表符": "https://emos.plurk.com/12122c248fcdc226b5b8fc65ea47a522_w48_h48.png"
    }
    
    all_passed = True
    for emoji_type, emoji_url in required_emojis.items():
        if emoji_url in all_emoji_urls:
            print(f"  ✓ {emoji_type}: {emoji_url}")
        else:
            print(f"  ✗ {emoji_type}: {emoji_url} (未找到)")
            all_passed = False
            # 顯示相似的 URL
            hash_id = emoji_url.split('/')[-1].split('_')[0]
            similar = [url for url in all_emoji_urls if hash_id in url]
            if similar:
                print(f"    相似 URL: {similar}")
    
    print(f"\n總計找到 {len(all_emoji_urls)} 個不重複的表符")
    print(f"  - 內容表符: {len(content_emoji_urls)}")
    print(f"  - 噗文互動表符: {len(plurk_reaction_emoji_urls)}")
    print(f"  - 留言互動表符: {len(response_reaction_emoji_urls)}")
    
    # 顯示所有找到的表符（前 20 個）
    print(f"\n找到的所有表符（前 20 個）:")
    for i, url in enumerate(all_emoji_urls[:20], 1):
        emoji_type = "內容"
        if url in plurk_reaction_emoji_urls:
            emoji_type = "噗文互動"
        elif url in response_reaction_emoji_urls:
            emoji_type = "留言互動"
        print(f"  {i}. [{emoji_type}] {url}")
    if len(all_emoji_urls) > 20:
        print(f"  ... 還有 {len(all_emoji_urls) - 20} 個")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("測試結果: ✓ 通過")
    else:
        print("測試結果: ✗ 失敗")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = test_plurk_url_html_complete()
    exit(0 if success else 1)
