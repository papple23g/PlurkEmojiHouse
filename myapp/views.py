# -*- coding: utf-8 -*-
from __future__ import unicode_literals

'''
from myapp.models import Emoji,CombindEmoji
from myapp.views import *

'''
from django.shortcuts import render
from django.http import HttpResponse
from myapp.models import *
from django.core import serializers
import urllib2
from taggit.models import Tag
TAGS = Tag.objects.all()

#定義動作:驗證和更正表符網址(v1.0)
def Correcting_emojiUrl(emoji_url):
    emoji_url=emoji_url.replace("*","")
    if ("s.plurk.com" in emoji_url) and (emoji_url.count(".")==3):
        #修正開頭不是https的url
        if emoji_url[:8]!="https://":
            if "emos.plurk.com" in emoji_url:
                emo_i=emoji_url.index("emos.plurk.com")
            else:
                emo_i=emoji_url.index("s.plurk.com")
            emoji_url="https://"+emoji_url[emo_i:]
        return emoji_url
    else:
        return False

def PlurkEmojiHouse(request):
    return render(request,"PlurkEmojiHouse.html",)

from django.forms.models import model_to_dict
import json

#定義動作，將QuerySet形式的表符串列轉化成字典串列，一個字典的key包含id,url,tags，其中tags內的標籤之間用逗號區隔
#會根據user_uid過濾tags : 去除含有收藏標籤開頭(__collectorUsers__)的標籤，但將符合user_uid的收藏標籤則轉為"__be_collected__"標籤，讓前端去處理
def EmojiDictList(Emoji_list,user_uid=None):
    Emoji_dict_list=[]
    if user_uid:
        for emoji in Emoji_list:
            Emoji_dict=model_to_dict(emoji)
            emoji_tags_names_filtered_list=[tag_name.replace("__collectorUsers__"+user_uid,"__be_collected__") for tag_name in emoji.tags.names() if (tag_name=="__collectorUsers__"+user_uid or (not tag_name.startswith("__collectorUsers__")))]
            Emoji_dict["tags"]=','.join(emoji_tags_names_filtered_list)
            Emoji_dict_list.append(Emoji_dict)
    else:
        for emoji in Emoji_list:
            Emoji_dict=model_to_dict(emoji)
            emoji_tags_names_filtered_list=[tag_name for tag_name in emoji.tags.names() if (not tag_name.startswith("__collectorUsers__"))]
            Emoji_dict["tags"]=','.join(emoji_tags_names_filtered_list)
            Emoji_dict_list.append(Emoji_dict)
    return Emoji_dict_list

#功能函數:輸入標籤，輸出表符字典串列，格式為[{"url":"...","id":[int],"tags":"A,B,..."}]
def search_by_tag(request):
    #獲取關鍵字與第幾頁面
    search_tag=request.GET.get('search_tag',"")
    i_page=int(request.GET.get('page','0'))
    user_uid=request.GET.get('user_uid',None)

    #若是使用hash數值搜尋相似圖片###
    if search_tag.startswith('__hash__'):
        #獲取指定要搜尋的emoji
        emoji_id=search_tag[len('__hash__'):]
        emoji_qlist=Emoji.objects.filter(id=emoji_id)
        #若該emoji存在
        if emoji_qlist:
            emoji=emoji_qlist[0]
            imagehash=emoji.getImagehash()
            threshold=10
            similar_emoji_list=[]
            for emoji in Emoji.objects.all():
                if (imagehash-emoji.getImagehash()<threshold):
                    similar_emoji_list.append(emoji)
            Emoji_dict_list=EmojiDictList(similar_emoji_list,user_uid)
            return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
        #若該emoji不存在
        else:
            return HttpResponse(u"沒有該圖片的搜尋結果")

    #若是使用一般標籤搜尋
    else:
        #獲取搜尋清單的區間
        num_of_emoji_per_page=int(request.GET.get('num_of_emoji_per_page',"20"))
        i_raw_top=i_page*num_of_emoji_per_page
        i_raw_bottom=i_raw_top+num_of_emoji_per_page
        #空字串的搜尋預設為顯示全部表符
        if search_tag=="":
            Emoji_list=Emoji.objects.all().order_by("-id")[i_raw_top:i_raw_bottom]
        #一般搜尋表符的情況    
        else:
            #區分逗號","分出多個標籤
            search_tag_list=[tag.strip() for tag in search_tag.split(",") if tag!=""]
            #進行集合篩選
            exec('Emoji_list=Emoji.objects'+''.join(['.filter(tags__name__in=[u"'+searth_tag_i_str+'"])' for searth_tag_i_str in search_tag_list])+'.order_by("-id")')
            Emoji_list=Emoji_list[i_raw_top:i_raw_bottom]
        #若有找到一個以上的結果，返回表符字典串列
        if Emoji_list:
            Emoji_dict_list=EmojiDictList(Emoji_list,user_uid)
            return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
        #沒有找到結果時
        else:
            #若已勾選「顯示我的收藏」
            if "__collectorUsers__" in search_tag:
                #若是顯示全部收藏的表符但沒有結果
                if search_tag.startswith(",__collectorUsers__"):
                    return HttpResponse(u"沒有收藏的表符哦!")
                #若是收藏的表符中找不到標籤結果
                else:
                    return HttpResponse(u"沒有符合 "+search_tag[:search_tag.index(",__collectorUsers__")]+u" 的搜尋結果")
            #若未勾選「顯示我的收藏」
            else:
                return HttpResponse(u"沒有符合 "+search_tag+u" 的搜尋結果")

#功能函數:輸入標籤，輸出表符結果頁數
def numOfEmojiPageBtn(request):
    num_of_emoji_per_page=int(request.GET.get('num_of_emoji_per_page',"20"))
    #獲取表符列表
    search_tag=request.GET.get('search_tag',"")
    #若表符列表為空字串，則計算全部表符需要幾頁
    if search_tag=="":
        num_of_btn=(Emoji.objects.count()-1)/num_of_emoji_per_page +1
    #若表符列表不為空字串，則計算搜尋結果全部表符需要幾頁
    else:
         #區分逗號","分出多個標籤
        search_tag_list=[tag.strip() for tag in search_tag.split(",") if tag!=""]
        #進行集合篩選
        exec('Emoji_list=Emoji.objects'+''.join(['.filter(tags__name__in=[u"'+searth_tag_i_str+'"])' for searth_tag_i_str in search_tag_list])+'.order_by("-id")')
        num_of_btn=(len(Emoji_list)-1)/num_of_emoji_per_page +1
    return HttpResponse(num_of_btn)
    
    
#功能函數，增加表符
def search_by_url(request):
    #必須已經更正過url開頭為https
    search_url=request.GET.get('search_url',"")
    user_uid=request.GET.get('user_uid',None)
    if ("https://emos.plurk.com/" in search_url) or ("https://s.plurk.com/" in search_url):
        Emoji_list=Emoji.objects.filter(url=search_url)
        #若表符已存在，則僅將該資料回傳表符字典
        if Emoji_list:
            Emoji_dict_list=EmojiDictList(Emoji_list,user_uid=user_uid)
            return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
        #若表符不存在，則新增該資料後再回傳表符字典
        else:
            try:
                #計算圖片hash數值
                imagehash=HashOfImage_inputUrl(search_url)
                imagehash_str=str(imagehash)
                Emoji.objects.create(url=search_url,imagehash_str=imagehash_str)
                Emoji_list=Emoji.objects.filter(url=search_url)
                Emoji_dict_list=EmojiDictList(Emoji_list,user_uid=user_uid)
                return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
            except:
                return HttpResponse(u"沒有符合 "+search_url+" 的搜尋結果(網址不正確或已失效)")
        
    else:
        return HttpResponse(u"沒有符合 "+search_url+" 的搜尋結果(網址不正確!)")

#功能函數，批量增加表符
def search_by_url_list(request):
    search_url_list_str=request.GET.get('search_url_list',"")
    search_url_list=search_url_list_str.split(",")
    Emoji_dict_list=[]
    for search_url in search_url_list:
        search_url=Correcting_emojiUrl(search_url)
        if search_url:
            search_url=search_url.strip()  #去除網址前後空白
            Emoji_obj_list=Emoji.objects.filter(url=search_url)
            #若表符已存在，則僅將該資料回傳表符字典
            if Emoji_obj_list:
                Emoji_dict=EmojiDictList(Emoji_obj_list)[0]
                Emoji_dict_list.append(Emoji_dict)
            #若表符不存在，則新增該資料後再回傳表符字典
            else:
                #嘗試新增圖片，若失敗就略過 (圖片網址失效時會被略過)
                try:
                    #計算圖片hash數值
                    imagehash=HashOfImage_inputUrl(search_url)
                    imagehash_str=str(imagehash)
                    Emoji.objects.create(url=search_url,imagehash_str=imagehash_str)
                    Emoji_obj_list=Emoji.objects.filter(url=search_url)
                    Emoji_dict=EmojiDictList(Emoji_obj_list)[0]
                    Emoji_dict_list.append(Emoji_dict)
                except:
                    pass
            
    if Emoji_dict_list:
        return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
    else:    
        return HttpResponse(u"沒有表符在此噗文中")
    
        
#功能函數，增加標籤
def emoji_add_tag(request):
    #獲取欲新增標籤的表符id，和要新增的表符字串(含逗號)
    emoji_id=request.GET.get('id',None)
    add_tag_str=request.GET.get('add_tag_str',None)
    #以逗號區分標嵌字串，並去除網址前後空白
    add_tag_list=[tag.strip() for tag in add_tag_str.split(",")]
    Emoji.objects.get(id=emoji_id).tags.add(*add_tag_list)
    return HttpResponse(emoji_id)

#功能函數，批量增加標籤
def emoji_list_add_tag(request):
    emoji_id_str_for_add_list_str=request.GET.get('emoji_id_str_for_add_list_str',None)
    tag_list_str=request.GET.get('tag_list_str',None)
    #將字串資料改成串列資料
    emoji_id_list=[int(emoji_id) for emoji_id in emoji_id_str_for_add_list_str.split(",")]
    #以逗號區分標嵌字串，並去除網址前後空白
    tag_list=[tag.strip() for tag in tag_list_str.split(",")] 
    #批量對表符增加多個相同標籤
    for emoji_id in emoji_id_list:
        Emoji.objects.get(id=emoji_id).tags.add(*tag_list)
    return HttpResponse('done')

#刪除標籤的功能函數
def delete_tag(request):
    emoji_id_str=request.GET.get('emoji_id',None)
    emoji_id=int(emoji_id_str)
    tag_name=request.GET.get('tag_name',None)
    Emoji.objects.get(id=emoji_id).tags.remove(tag_name)

    #若該標籤的被標籤數為零，則徹底刪除這個標籤
    tag=Tag.objects.get(name=tag_name)
    if tag.taggit_taggeditem_items.count()==0:
        tag.delete()

    return HttpResponse(tag_name)

#功能函數，搜尋標籤
def search_tags(request):
    #分析請求，獲取要搜尋的關鍵字列表
    search_tag_list_str=request.GET.get('search_tag',"")
    #過濾想要搜尋的關鍵字列表:去除空白和含有使用者收藏標籤的開頭關鍵字
    search_tag_list=[tag.strip() for tag in search_tag_list_str.split(",") if (tag!="" and ("__collectorUsers__" not in tag))]
    
    tags_list=[]
    num_of_tagged_list=[]
    for search_tag in search_tag_list:
        #將有包含關鍵字的標籤放入tags_list
        tags_list_QuerySet=TAGS.filter(name__icontains=search_tag)
        #過濾標籤搜尋結果:去除含有使用者收藏標籤的開頭關鍵字
        tags_list_QuerySet=[tag for tag in tags_list_QuerySet if ("__collectorUsers__" not in tag.name)]
        for tag in tags_list_QuerySet:
            if tag not in tags_list: #不納入重複的標籤
                tags_list.append(tag.name)
                #將標籤對應的【被標籤數】append到tags_list
                num_of_tagged_list.append(tag.taggit_taggeditem_items.count())
    tags_list_and_num_of_tagged_list=[tags_list,num_of_tagged_list]
    return HttpResponse(json.dumps(tags_list_and_num_of_tagged_list), content_type="application/json")

#功能函數，讀取站內資料:表符數量和標籤數量
def NumOfEmoji_and_NumOfTag(request):
    numOfEmoji=Emoji.objects.count()
    numOfTag=Tag.objects.count()
    return HttpResponse(json.dumps([numOfEmoji,numOfTag]), content_type="application/json")


#功能函數，用爬蟲獲取噗文網址的原始碼
import requests
def PlurkUrlHtml(request):
    #獲取噗首原始碼以及該噗文的ID
    plurk_url=request.GET.get('plurk_url',None)
    headers={"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)", "Referer": "http://example.com"}
    res=requests.get(plurk_url, headers=headers, timeout=10)
    res_text=res.text
    plurk_id_sandStr=', "plurk_id": '
    res_text_plurkIdSandStr_i=res_text.index(plurk_id_sandStr)
    plurk_id_str=res_text[res_text_plurkIdSandStr_i+len(plurk_id_sandStr) : res_text.index(",",res_text_plurkIdSandStr_i+1) ]

    #根據該噗文的ID進行POST請求，獲取回應噗文的字典資料
    post_data_dict={
        'plurk_id':plurk_id_str,
        'count':'1000',
    }
    url=r'https://www.plurk.com/Responses/get'
    res = requests.post(url,data=post_data_dict)
    res_dict=json.loads(res.text)

    #將回應噗文的HTML原始碼內容和噗首原始碼自串接在一起送出
    responses_dict_list=res_dict['responses']
    for responses_dict in responses_dict_list:
        content_str=responses_dict['content']
        #排除沒有使用表符的回應
        if "https://emos.plurk.com/" in content_str:
            res_text+=content_str
    #print(res_text)

    return HttpResponse(res_text)

#功能函數:新增組合表符
def AddCombindEmoji(request):
    #獲取並分析表符的集合網址串列
    combind_url=request.GET.get('combind_url',None)
    combind_url_splitted_str=combind_url.replace("**","|").replace("*","")
    emoji_url_set=list(set(combind_url_splitted_str.split("|")))
    #檢查該組合表符是否已經存在，若不存在就新增該組合表符
    if not CombindEmoji.objects.filter(combind_url=combind_url):
        combindEmoji=CombindEmoji.objects.create(combind_url=combind_url)
        combindEmoji.emoji_url_set.add(*emoji_url_set)
    return HttpResponse(json.dumps(emoji_url_set), content_type="application/json")

#功能函數:刪除組合表符
def DeleteCombindEmoji(request):
    #獲取表符的集合網址串列
    combind_url=request.GET.get('combind_url',None)
    CombindEmoji.objects.filter(combind_url=combind_url)[0].delete()
    return HttpResponse('done', content_type="application/json")

#功能函數:搜尋組合表符
def SearchCombindEmoji(request):
    emoji_url=request.GET.get('emoji_url',None)
    combind_url_list=[combindEmoji.combind_url for combindEmoji in CombindEmoji.objects.filter(emoji_url_set__name__in=[emoji_url])]
    #print "emoji_url:",emoji_url,"\ncombind_url_list:",combind_url_list
    return HttpResponse(json.dumps(combind_url_list), content_type="application/json")
