# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from myapp.models import Emoji
from django.core import serializers
import urllib2
from taggit.models import Tag
TAGS = Tag.objects.all()

def home(request):
    return render(request,"home.html",)

def testHttpResponse(request):
    content='''
    This is page1.
    '''
    return HttpResponse(content)

def testRender(request):
    name='Peter'
    return render(request,"test_render.html", {'name': name})

def PlurkEmojiHouse(request):
    return render(request,"PlurkEmojiHouse.html",)

def testBrython(request):
    return render(request,"Brython.html",)

from django.forms.models import model_to_dict
import json

#定義動作，將QuerySet形式的表符串列轉化成字典串列，一個字典的key包含id,url,tags，其中tags內的標籤之間用逗號區隔
def EmojiDictList(Emoji_list):
    Emoji_dict_list=[]
    for emoji in Emoji_list:
        Emoji_dict=model_to_dict(emoji)
        Emoji_dict["tags"]=','.join(emoji.tags.names())
        Emoji_dict_list.append(Emoji_dict)
    return Emoji_dict_list

#功能函數:輸入標籤，輸出表符字典串列，格式為[{"url":"...","id":[int],tags":"A,B,..."}]
def search_by_tag(request):
    #獲取關鍵字與第幾頁面
    search_tag=request.GET.get('search_tag',"")
    i_page=int(request.GET.get('page','0'))
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
        searth_tag_list=[tag for tag in search_tag.split(",") if tag!=""]
        #進行集合篩選
        exec('Emoji_list=Emoji.objects'+''.join(['.filter(tags__name__in=[u"'+searth_tag_i_str+'"])' for searth_tag_i_str in searth_tag_list])+'.order_by("-id")')
        Emoji_list=Emoji_list[i_raw_top:i_raw_bottom]
    #若有找到一個以上的結果，返回表符字典串列
    if Emoji_list:
        Emoji_dict_list=EmojiDictList(Emoji_list)
        return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
    else:
        return HttpResponse(u"沒有符合 "+search_tag+" 的搜尋結果")

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
        search_tag_list=search_tag.split(",")
        exec('Emoji_list=Emoji.objects'+''.join(['.filter(tags__name__in=[u"'+tag+'"])' for tag in search_tag_list])+'.order_by("-id")')
        num_of_btn=(len(Emoji_list)-1)/num_of_emoji_per_page +1
    return HttpResponse(num_of_btn)
    
    
#功能函數，增加表符
def search_by_url(request):
    #必須已經更正過url開頭為https
    search_url=request.GET.get('search_url',"")
    if ("https://emos.plurk.com/" in search_url) or ("https://s.plurk.com/" in search_url):
        Emoji_list=Emoji.objects.filter(url=search_url)
        #若表符已存在，則僅將該資料回傳表符字典
        if Emoji_list:
            Emoji_dict_list=EmojiDictList(Emoji_list)
        #若表符不存在，則新增該資料後再回傳表符字典
        else:
            Emoji.objects.create(url=search_url)
            Emoji_list=Emoji.objects.filter(url=search_url)
            Emoji_dict_list=EmojiDictList(Emoji_list)
        return HttpResponse(json.dumps(Emoji_dict_list), content_type="application/json")
    else:
        return HttpResponse(u"沒有符合 "+search_url+" 的搜尋結果(網址不正確!)")

def test(request):
    return HttpResponse(u"沒HERE!")

#功能函數，批量增加表符
def search_by_url_list(request):
    search_url_list_str=request.GET.get('search_url_list',"")
    search_url_list=search_url_list_str.split(",")
    Emoji_dict_list=[]
    for search_url in search_url_list:
        if ("https://emos.plurk.com/" in search_url):
            search_url=search_url.strip()  #去除網址前後空白
            Emoji_obj_list=Emoji.objects.filter(url=search_url)
            #若表符已存在，則僅將該資料回傳表符字典
            if Emoji_obj_list:
                Emoji_dict=EmojiDictList(Emoji_obj_list)[0]
            #若表符不存在，則新增該資料後再回傳表符字典
            else:
                Emoji.objects.create(url=search_url)
                Emoji_obj_list=Emoji.objects.filter(url=search_url)
                Emoji_dict=EmojiDictList(Emoji_obj_list)[0]
            Emoji_dict_list.append(Emoji_dict)
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

##功能函數，批量增加標籤
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
    search_tag_list=[tag.strip() for tag in search_tag_list_str.split(",") if tag!=""] #.strip() 去除網址前後空白
    
    tags_list=[]
    num_of_tagged_list=[]
    for search_tag in search_tag_list:
        #將有包含關鍵字的標籤放入tags_list
        tags_list_QuerySet=TAGS.filter(name__icontains=search_tag)
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
    plurk_url=request.GET.get('plurk_url',None)
    headers={"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)", "Referer": "http://example.com"}
    res=requests.get(plurk_url, headers=headers, timeout=10)
    return HttpResponse(res)