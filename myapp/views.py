# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from functools import reduce

import certifi
import requests
from django.forms.models import model_to_dict

'''
from myapp.models import *
from taggit.models import Tag
from myapp.views import *

'''
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from taggit.models import Tag

from myapp.models import CombindEmoji, Emoji, HashOfImage_inputUrl

TAGS = Tag.objects.all()

# 定義動作:驗證和更正表符網址(v1.0)


def Correcting_emojiUrl(emoji_url):
    emoji_url = emoji_url.replace("*", "")
    if ("s.plurk.com" in emoji_url) and (emoji_url.count(".") == 3):
        # 修正開頭不是https的url
        if emoji_url[:8] != "https://":
            if "emos.plurk.com" in emoji_url:
                emo_i = emoji_url.index("emos.plurk.com")
            else:
                emo_i = emoji_url.index("s.plurk.com")
            emoji_url = "https://"+emoji_url[emo_i:]
        return emoji_url
    else:
        return False


def PlurkEmojiHouse(request):
    return render(request, "PlurkEmojiHouse.html",)


# 定義動作，將QuerySet形式的表符串列轉化成字典串列，一個字典的key包含id,url,tags，其中tags內的標籤之間用逗號區隔
# 會根據user_uid過濾tags : 去除含有收藏標籤開頭(__collectorUsers__)的標籤，但將符合user_uid的收藏標籤則轉為"__be_collected__"標籤，讓前端去處理
def EmojiDictList(Emoji_list, user_uid=None):
    Emoji_dict_list = []
    if user_uid:
        for emoji in Emoji_list:
            Emoji_dict = model_to_dict(emoji)
            emoji_tags_names_filtered_list = [tag_name.replace("__collectorUsers__"+user_uid, "__be_collected__") for tag_name in emoji.tags.names(
            ) if (tag_name == "__collectorUsers__"+user_uid or (not tag_name.startswith("__collectorUsers__")))]
            Emoji_dict["tags"] = ','.join(emoji_tags_names_filtered_list)
            Emoji_dict_list.append(Emoji_dict)
    else:
        for emoji in Emoji_list:
            Emoji_dict = model_to_dict(emoji)
            emoji_tags_names_filtered_list = [tag_name for tag_name in emoji.tags.names(
            ) if (not tag_name.startswith("__collectorUsers__"))]
            Emoji_dict["tags"] = ','.join(emoji_tags_names_filtered_list)
            Emoji_dict_list.append(Emoji_dict)
    return Emoji_dict_list

# 功能函數:輸入標籤，輸出表符字典串列，格式為[{"url":"...","id":[int],"tags":"A,B,..."}]


def search_by_tag(request):
    # 獲取關鍵字與第幾頁面
    search_tag = request.GET.get('search_tag', "")
    i_page = int(request.GET.get('page', '0'))
    user_uid = request.GET.get('user_uid', None)

    # 若是使用hash數值搜尋相似圖片
    if search_tag.startswith('__hash__'):
        # 獲取指定要搜尋的emoji
        emoji_id = search_tag[len('__hash__'):]
        emoji_qlist = Emoji.objects.filter(id=emoji_id)
        # 若該emoji存在
        if emoji_qlist:
            emoji = emoji_qlist[0]
            imagehash = emoji.getImagehash()
            threshold = 8
            similar_emoji_list = []
            for emoji in Emoji.objects.all():
                try:
                    diff_int = imagehash-emoji.getImagehash()
                    if (diff_int < threshold):
                        similar_emoji_list.append(emoji)
                except:
                    pass
            Emoji_dict_list = EmojiDictList(similar_emoji_list, user_uid)
            return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
        # 若該emoji不存在
        else:
            return HttpResponse(u"沒有該圖片的搜尋結果")

    # 若是使用一般標籤搜尋
    else:
        # 獲取搜尋清單的區間
        num_of_emoji_per_page = int(
            request.GET.get('num_of_emoji_per_page', "20"))
        i_raw_top = i_page*num_of_emoji_per_page
        i_raw_bottom = i_raw_top+num_of_emoji_per_page

        # 設置表符模組物件
        Emoji_objects = Emoji.objects

        # 獲取是否勾選組合表符
        search_in_combindEmoji_bool = (",__showCombindEmojis__" in search_tag)
        # 若有勾選組合表符
        if search_in_combindEmoji_bool:
            # 則將關鍵字標籤去除避免錯誤發生
            search_tag = search_tag.replace(",__showCombindEmojis__", "")
            # 獲取所有組合表符的emoji_url
            combind_emoji_url_list = list(set(tag.name for tag in Tag.objects.filter(
                name__icontains="https://emos.plurk.com/")))
            # 獲取為組合表符的emoji_qlist
            Emoji_objects = Emoji.objects.filter(reduce(lambda x, y: x | y, [Q(
                url=combind_emoji_url) for combind_emoji_url in combind_emoji_url_list]))

        # 空字串的搜尋預設為顯示全部表符
        if search_tag == "":
            Emoji_list = Emoji_objects.all().order_by(
                "-id")[i_raw_top:i_raw_bottom]
        # 一般搜尋表符的情況
        else:
            # 區分逗號","分出多個標籤
            search_tag_str_set = {
                tag.strip()
                for tag in search_tag.split(",") if tag != ""
            }
            # 進行集合篩選
            Emoji_list = (
                Emoji_objects.filter(tags__name__in=search_tag_str_set)
                .annotate(num_tags=Count('tags'))
                .filter(num_tags=len(search_tag_str_set))
            ).order_by("-id")[i_raw_top:i_raw_bottom]
        # 若有找到一個以上的結果，返回表符字典串列
        if Emoji_list:
            Emoji_dict_list = EmojiDictList(Emoji_list, user_uid)
            return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
        # 沒有找到結果時
        else:
            # 若已勾選「顯示我的收藏」
            if "__collectorUsers__" in search_tag:
                # 若是顯示全部收藏的表符但沒有結果
                if search_tag.startswith(",__collectorUsers__"):
                    return HttpResponse(u"沒有收藏的表符哦!")
                # 若是收藏的表符中找不到標籤結果
                else:
                    return HttpResponse(u"沒有符合 "+search_tag[:search_tag.index(",__collectorUsers__")]+u" 的搜尋結果")
            # 若未勾選「顯示我的收藏」
            else:
                return HttpResponse(u"沒有符合 "+search_tag+u" 的搜尋結果")

# 功能函數:輸入標籤，輸出表符結果頁數


def numOfEmojiPageBtn(request):
    num_of_emoji_per_page = int(request.GET.get('num_of_emoji_per_page', "20"))
    # 獲取表符列表
    search_tag = request.GET.get('search_tag', "")

    # 設置表符模組物件
    Emoji_objects = Emoji.objects

    # 獲取是否勾選組合表符
    search_in_combindEmoji_bool = (",__showCombindEmojis__" in search_tag)
    # 若有勾選組合表符
    if search_in_combindEmoji_bool:
        # 則將關鍵字標籤去除避免錯誤發生
        search_tag = search_tag.replace(",__showCombindEmojis__", "")
        # 獲取所有組合表符的emoji_url
        combind_emoji_url_list = list(set(tag.name for tag in Tag.objects.filter(
            name__icontains="https://emos.plurk.com/")))
        # 獲取為組合表符的emoji_qlist
        Emoji_objects = Emoji_objects.filter(reduce(lambda x, y: x | y, [Q(
            url=combind_emoji_url) for combind_emoji_url in combind_emoji_url_list]))

    # 若表符列表為空字串，則計算全部表符需要幾頁
    if search_tag == "":
        num_of_btn = (Emoji_objects.count()-1)/num_of_emoji_per_page + 1
    # 若表符列表不為空字串，則計算搜尋結果全部表符需要幾頁
    else:
        # 區分逗號","分出多個標籤
        search_tag_str_set = {
            tag.strip()
            for tag in search_tag.split(",") if tag != ""
        }
        # 進行集合篩選
        Emoji_list_count = (
            Emoji_objects.filter(tags__name__in=search_tag_str_set)
            .annotate(num_tags=Count('tags'))
            .filter(num_tags=len(search_tag_str_set))
            .count()
        )
        num_of_btn = (Emoji_list_count-1)/num_of_emoji_per_page + 1
    return HttpResponse(int(num_of_btn))


# 功能函數，增加表符
def search_by_url(request):
    # 必須已經更正過url開頭為https
    search_url = request.GET.get('search_url', "")
    user_uid = request.GET.get('user_uid', None)
    if ("https://emos.plurk.com/" in search_url) or ("https://s.plurk.com/" in search_url):
        Emoji_list = Emoji.objects.filter(url=search_url)
        # 若表符已存在，則僅將該資料回傳表符字典
        if Emoji_list:
            Emoji_dict_list = EmojiDictList(Emoji_list, user_uid=user_uid)
            return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
        # 若表符不存在，則新增該資料後再回傳表符字典
        else:
            try:
                # 計算圖片hash數值
                imagehash = HashOfImage_inputUrl(search_url)
                imagehash_str = str(imagehash)
                Emoji.objects.create(
                    url=search_url, imagehash_str=imagehash_str)
                Emoji_list = Emoji.objects.filter(url=search_url)
                Emoji_dict_list = EmojiDictList(Emoji_list, user_uid=user_uid)
                return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
            except Exception as e:
                print(f"{e!r}")
                return HttpResponse(u"沒有符合 "+search_url+" 的搜尋結果(網址不正確或已失效)")

    else:
        return HttpResponse(u"沒有符合 "+search_url+" 的搜尋結果(網址不正確!)")

# 功能函數，批量增加表符


def search_by_url_list(request):
    search_url_list_str = request.GET.get('search_url_list', "")
    search_url_list = search_url_list_str.split(",")
    Emoji_dict_list = []
    for search_url in search_url_list:
        search_url = Correcting_emojiUrl(search_url)
        if search_url:
            search_url = search_url.strip()  # 去除網址前後空白
            Emoji_obj_list = Emoji.objects.filter(url=search_url)
            # 若表符已存在，則僅將該資料回傳表符字典
            if Emoji_obj_list:
                Emoji_dict = EmojiDictList(Emoji_obj_list)[0]
                Emoji_dict_list.append(Emoji_dict)
            # 若表符不存在，則新增該資料後再回傳表符字典
            else:
                # 嘗試新增圖片，若失敗就略過 (圖片網址失效時會被略過)
                try:
                    # 計算圖片hash數值
                    imagehash = HashOfImage_inputUrl(search_url)
                    imagehash_str = str(imagehash)
                    Emoji.objects.create(
                        url=search_url, imagehash_str=imagehash_str)
                    Emoji_obj_list = Emoji.objects.filter(url=search_url)
                    Emoji_dict = EmojiDictList(Emoji_obj_list)[0]
                    Emoji_dict_list.append(Emoji_dict)
                except:
                    pass

    if Emoji_dict_list:
        return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
    else:
        return HttpResponse(u"沒有表符在此噗文中")


# 功能函數，增加標籤
def emoji_add_tag(request):
    # 獲取欲新增標籤的表符id，和要新增的表符字串(含逗號)
    emoji_id = request.GET.get('id', None)
    add_tag_str = request.GET.get('add_tag_str', None)
    # 以逗號區分標嵌字串，並去除網址前後空白
    add_tag_list = [tag.strip() for tag in add_tag_str.split(",")]
    Emoji.objects.get(id=emoji_id).tags.add(*add_tag_list)
    return HttpResponse(emoji_id)

# 功能函數，批量增加標籤


def emoji_list_add_tag(request):
    emoji_id_str_for_add_list_str = request.GET.get(
        'emoji_id_str_for_add_list_str', None)
    tag_list_str = request.GET.get('tag_list_str', None)
    # 將字串資料改成串列資料
    emoji_id_list = [int(emoji_id)
                     for emoji_id in emoji_id_str_for_add_list_str.split(",")]
    # 以逗號區分標嵌字串，並去除網址前後空白
    tag_list = [tag.strip() for tag in tag_list_str.split(",")]
    # 批量對表符增加多個相同標籤
    for emoji_id in emoji_id_list:
        Emoji.objects.get(id=emoji_id).tags.add(*tag_list)
    return HttpResponse('done')

# 刪除標籤的功能函數


def delete_tag(request):
    emoji_id_str = request.GET.get('emoji_id', None)
    emoji_id = int(emoji_id_str)
    tag_name = request.GET.get('tag_name', None)
    Emoji.objects.get(id=emoji_id).tags.remove(tag_name)

    # 若該標籤的被標籤數為零，則徹底刪除這個標籤
    tag = Tag.objects.get(name=tag_name)
    if tag.taggit_taggeditem_items.count() == 0:
        tag.delete()

    return HttpResponse(tag_name)

# 功能函數，搜尋標籤


def search_tags(request):
    # 分析請求，獲取要搜尋的關鍵字列表
    search_tag_list_str = request.GET.get('search_tag', "")
    # 過濾想要搜尋的關鍵字列表:去除空白和含有使用者收藏標籤的開頭關鍵字
    search_tag_list = [tag.strip() for tag in search_tag_list_str.split(
        ",") if (tag != "" and ("__collectorUsers__" not in tag))]

    tags_list = []
    num_of_tagged_list = []
    for search_tag in search_tag_list:
        # 將有包含關鍵字的標籤放入tags_list
        tags_list_QuerySet = TAGS.filter(name__icontains=search_tag)
        # 過濾標籤搜尋結果:去除含有使用者收藏標籤的開頭關鍵字以及去除組合表符網址標籤
        tags_list_QuerySet = [tag for tag in tags_list_QuerySet if (
            "__collectorUsers__" not in tag.name) and ("https://emos.plurk.com/" not in tag.name)]
        for tag in tags_list_QuerySet:
            if tag not in tags_list:  # 不納入重複的標籤
                tags_list.append(tag.name)
                # 將標籤對應的【被標籤數】append到tags_list
                num_of_tagged_list.append(tag.taggit_taggeditem_items.count())
    tags_list_and_num_of_tagged_list = [tags_list, num_of_tagged_list]
    return HttpResponse(json.dumps(tags_list_and_num_of_tagged_list), content_type="application/json")

# 功能函數，讀取站內資料:表符數量和標籤數量


def NumOfEmoji_and_NumOfTag(request):
    numOfEmoji = Emoji.objects.count()
    numOfTag = Tag.objects.count()
    return HttpResponse(json.dumps([numOfEmoji, numOfTag]), content_type="application/json")


# 功能函數，從 HTML 中提取表符 URL


def extract_emoji_urls_from_html(html_text: str) -> list[str]:
    """
    從 HTML 文本中提取所有表符 URL
    
    支援的格式：
    - https://emos.plurk.com/...
    - //emos.plurk.com/... (protocol-relative)
    - https://s.plurk.com/...
    - //s.plurk.com/...
    
    Returns:
        list[str]: 正規化後的表符 URL 列表（去重且保持順序）
    """
    import re
    
    # 匹配所有可能的表符 URL 格式
    # 包含 protocol-relative URL (//)、完整 URL (https://)
    pattern = r'(?:https?:)?//(?:emos\.plurk\.com|s\.plurk\.com)/[a-zA-Z0-9_]+_w\d+_h\d+\.(png|gif|jpg|jpeg)'
    
    matches = re.findall(pattern, html_text)
    # findall 會返回 group，需要重新搜尋完整 URL
    all_matches = re.finditer(pattern, html_text)
    emoji_urls_raw = [match.group(0) for match in all_matches]
    
    # 使用 Correcting_emojiUrl 正規化每個 URL
    emoji_urls_normalized = []
    for url in emoji_urls_raw:
        corrected = Correcting_emojiUrl(url)
        if corrected:
            emoji_urls_normalized.append(corrected)
    
    # 去重但保持順序
    unique_urls = list(dict.fromkeys(emoji_urls_normalized))
    return unique_urls


# 功能函數，從 reactions 數據中提取表符 URL


def extract_emoji_urls_from_reactions(reactions_data, data_format='list') -> list[str]:
    """
    從 reactions 數據中提取表符 URL
    
    Args:
        reactions_data: reactions 數據（列表或字典）
        data_format: 'list' 或 'summary' 格式
            - 'list': reaction_summaries 格式 [{"reactions": [...]}]
            - 'summary': plurk summary 格式 {"summaries": [{"reactions": [...]}]}
    
    Returns:
        list[str]: 表符 URL 列表
    """
    try:
        # 根據格式統一獲取 items 列表
        if data_format == 'summary':
            items = reactions_data.get("summaries", []) if isinstance(reactions_data, dict) else []
        else:
            items = reactions_data if isinstance(reactions_data, list) else []
        
        # 提取符合條件的表符 URL
        return [
            url
            for item in items
            if isinstance(item, dict)
            for reaction in item.get('reactions', [])
            if (url := reaction.get('emoticon', {}).get('url'))
            and url.startswith("https://emos.plurk.com/")
        ]
    except Exception as e:
        print(f"提取互動表符時發生錯誤: {e!r}")
        return []


def chunked(iterable: list, size: int):
    for idx in range(0, len(iterable), size):
        yield iterable[idx: idx + size]


def fetch_legacy_responses(plurk_id: int, start_response_id: int, headers: dict, max_iterations: int = 32) -> tuple[list, list[int]]:
    legacy_url = "https://www.plurk.com/Responses/get"
    if start_response_id is None:
        return [], []

    collected = []
    response_ids = []
    known_ids = set()
    from_id = start_response_id
    previous_last_id = None

    for _ in range(max_iterations):
        payload = {"plurk_id": plurk_id, "from_response_id": from_id}
        try:
            res = requests.post(
                legacy_url,
                headers=headers,
                json=payload,
                timeout=10,
                verify=certifi.where(),
            )
            batch = res.json().get("responses", [])
        except Exception as e:
            print(f"獲取 legacy 回應失敗: {e!r}")
            break

        if not batch:
            break

        new_items = []
        for item in batch:
            rid = item.get("id")
            if not rid or rid in known_ids:
                continue
            known_ids.add(rid)
            new_items.append(item)
            response_ids.append(rid)

        if not new_items:
            break

        collected.extend(new_items)
        last_id = batch[-1].get("id")
        if not last_id or last_id == previous_last_id:
            break

        previous_last_id = last_id
        from_id = last_id + 1

    return collected, response_ids


def fetch_response_reaction_urls(plurk_id: int, response_ids: list[int], headers: dict, chunk_size: int = 100) -> list[str]:
    if not response_ids:
        return []

    url = f"https://www.plurk.com/v2/reaction/plurk/{plurk_id}/response/summary"
    collected_urls: list[str] = []
    for chunk in chunked(response_ids, chunk_size):
        try:
            res = requests.post(
                url,
                headers=headers,
                json={"response_ids": chunk},
                timeout=10,
                verify=certifi.where(),
            )
            res_dict = res.json()
            collected_urls.extend(extract_emoji_urls_from_reactions(res_dict, data_format="summary"))
        except Exception as e:
            print(f"獲取回應互動表符失敗: {e!r}")
    return collected_urls


# 功能函數，獲取噗文的互動表符 URL 列表


def get_reaction_emoji_urls(plurk_id: int) -> list[str]:
    url = "https://www.plurk.com/v2/reaction/plurk/summary"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)",
        "Content-Type": "application/json",
    }
    data = {"plurk_ids": [plurk_id]}
    
    try:
        res = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10,
            verify=certifi.where(),
        )
        res_dict = res.json()
        
        # 使用通用函數提取表符 URL
        return extract_emoji_urls_from_reactions(res_dict, data_format='summary')
    except Exception as e:
        print(f"獲取互動表符失敗: {e!r}")
        return []


# 功能函數，用爬蟲獲取噗文網址的原始碼


def PlurkUrlHtml(request):
    # 獲取噗首原始碼以及該噗文的ID
    plurk_url = request.GET.get('plurk_url', None)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)", "Referer": "http://example.com"}
    res = requests.get(plurk_url, headers=headers,
                       timeout=10, verify=certifi.where())
    res_text = res.text
    plurk_id_sandStr = ', "plurk_id": '
    res_text_plurkIdSandStr_i = res_text.index(plurk_id_sandStr)
    plurk_id_str = res_text[res_text_plurkIdSandStr_i +
                            len(plurk_id_sandStr): res_text.index(",", res_text_plurkIdSandStr_i+1)]

    # 根據該噗文的ID進行請求，獲取所有回應噗文的數據（優先採用 legacy API）
    seen_url = f'https://www.plurk.com/v2/plurk/{plurk_id_str}/responses/seen'
    plurk_id_int = int(plurk_id_str)
    seen_responses = []
    seen_reaction_summaries = []
    start_response_id = None

    try:
        seen_res = requests.get(seen_url, headers=headers, timeout=10, verify=certifi.where())
        seen_data = seen_res.json()
        seen_responses = seen_data.get('responses', [])
        seen_reaction_summaries = seen_data.get('reaction_summaries', [])
        if seen_responses:
            start_response_id = seen_responses[0].get('id')
    except Exception as e:
        print(f"獲取回應概覽失敗: {e!r}")

    legacy_responses, legacy_response_ids = fetch_legacy_responses(
        plurk_id_int,
        start_response_id,
        headers,
    )

    if not legacy_responses and seen_responses:
        legacy_responses = seen_responses
        legacy_response_ids = [resp.get('id') for resp in seen_responses if resp.get('id')]

    for responses_dict in legacy_responses:
        content_str = responses_dict.get('content', '')
        if "https://emos.plurk.com/" in content_str:
            res_text += content_str

    response_reaction_urls = []
    if legacy_response_ids:
        response_reaction_urls = fetch_response_reaction_urls(plurk_id_int, legacy_response_ids, headers)

    if not response_reaction_urls and seen_reaction_summaries:
        response_reaction_urls = extract_emoji_urls_from_reactions(seen_reaction_summaries, data_format='list')

    for emoji_url in response_reaction_urls:
        res_text += f'<img class="emoticon_my" src="{emoji_url}">'
    
    # 獲取噗文的互動表符並加入到返回的 HTML 中
    try:
        plurk_id_int = int(plurk_id_str)
        reaction_emoji_urls = get_reaction_emoji_urls(plurk_id_int)
        for emoji_url in reaction_emoji_urls:
            # 將互動表符 URL 轉換成 IMG 標籤格式，與現有表符格式一致
            res_text += f'<img class="emoticon_my" src="{emoji_url}">'
    except Exception as e:
        print(f"處理互動表符時發生錯誤: {e!r}")
    
    # 從 HTML 中提取所有表符 URL（包含投票選項等處的表符）
    try:
        html_emoji_urls = extract_emoji_urls_from_html(res_text)
        # 收集已經加入的表符 URL（避免重複加入）
        existing_urls = set()
        import re
        existing_pattern = r'<img[^>]+src="(https://(?:emos|s)\.plurk\.com/[^"]+)"'
        for match in re.finditer(existing_pattern, res_text):
            existing_urls.add(match.group(1))
        
        # 補上尚未加入的表符
        for emoji_url in html_emoji_urls:
            if emoji_url not in existing_urls:
                res_text += f'<img class="emoticon_my" src="{emoji_url}">'
                existing_urls.add(emoji_url)
    except Exception as e:
        print(f"從 HTML 提取表符時發生錯誤: {e!r}")
    
    # print(res_text)

    return HttpResponse(res_text)

# 功能函數:新增組合表符


def AddCombindEmoji(request):
    # 獲取並分析表符的集合網址串列
    combind_url = request.GET.get('combind_url', None)
    combind_url_splitted_str = combind_url.replace("**", "|").replace("*", "")
    emoji_url_set = list(set(combind_url_splitted_str.split("|")))
    # 檢查該組合表符是否已經存在，若不存在就新增該組合表符
    if not CombindEmoji.objects.filter(combind_url=combind_url):
        combindEmoji = CombindEmoji.objects.create(combind_url=combind_url)
        combindEmoji.emoji_url_set.add(*emoji_url_set)
    return HttpResponse(json.dumps(emoji_url_set), content_type="application/json")

# 功能函數:刪除組合表符


def DeleteCombindEmoji(request):
    # 獲取表符的集合網址串列
    combind_url = request.GET.get('combind_url', None)
    CombindEmoji.objects.filter(combind_url=combind_url)[0].delete()
    return HttpResponse('done', content_type="application/json")

# 功能函數:搜尋組合表符


def SearchCombindEmoji(request):
    emoji_url = request.GET.get('emoji_url', None)
    combind_url_list = [combindEmoji.combind_url for combindEmoji in CombindEmoji.objects.filter(
        emoji_url_set__name__in=[emoji_url])]
    # print "emoji_url:",emoji_url,"\ncombind_url_list:",combind_url_list
    return HttpResponse(json.dumps(combind_url_list), content_type="application/json")
