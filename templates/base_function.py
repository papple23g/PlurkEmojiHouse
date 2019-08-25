"""
負責基本函式或共同的函式
"""

from browser import window,doc,ajax,alert,bind,timer,confirm
from browser.html import *
import json
import copy

#引渡Javascript印出資料log語法
log=window.console.log

#引渡Javascript物件:firebase.database
firebase=window.firebase
database=firebase.database()

#定義動作:複製文字 #不需要建立外部額外元素
def CopyTextToClipborad(string):
    textarea_elt_forCopyText=TEXTAREA()
    textarea_elt_forCopyText.text=string
    doc<=textarea_elt_forCopyText
    textarea_elt_forCopyText.select()
    doc.execCommand("copy")
    textarea_elt_forCopyText.remove()

#定義功能函數，搜尋符和三明治文字夾層，回傳內容列表
def SandwichWord_list(sandWord,wichWord,text):
    len_sandWord=len(sandWord)
    len_wichWord=len(wichWord)
    com_list=[]
    i=0
    while i<len(text):
        if sandWord in text[i:]:
            i_sandWord=text.index(sandWord,i)
            i_wichWord=text.index(wichWord,i_sandWord+len(sandWord))
            com_str=text[i_sandWord+len_sandWord:i_wichWord]
            com_list.append(com_str)
            i=i_wichWord+len_wichWord
        else:
            break
    return com_list

#定義功能函數:增加CSS樣式字串
def AddStyle(style_str):
    style_elt=doc.select('head style')[0]
    style_elt.text+=style_str

#定義功能函數:找到對應tagName的父元素
def ParentElt(elt,parent_tagName):
    while (elt.tagName!=parent_tagName):
        elt=elt.parent
    return elt

#定義動作:將元素設定為游標在上方可顯示文字(預設:黑底白字,滑鼠覆蓋才顯示文字)
def DIV_showTipText(
    elt,tipText,
    tipText_clicked="",
    backgroundColor="black",
    textColor="white",
    show_ev_list=["mouseover"],
    hide_ev_list=["mouseout"],
    width="120px",
    tip_margin_left='10px',
    trangle_margin_left='-50px',
    ):
    #設定提示文字版樣式
    span_tip_elt=SPAN(tipText,Class="tooltiptext")
    span_tip_elt.style={
            'visibility':'hidden',
            'width':f'{width}',
            'background-color':f'{backgroundColor}',
            'color':f'{textColor}',
            'text-align':'center',
            'border-radius':'6px',
            'padding':'5px 0',
            'position':'absolute',
            'z-index':'12',
            'bottom':'100%',
            'left':'50%',
            'margin-left':tip_margin_left,
        }
    #設定對話框尖端物體(三角元件)樣式
    span_trangle_elt=SPAN("",Class="span_tooltip_trangle")
    span_trangle_elt.style={
        'position':'absolute',
        'top':'100%',
        'left':'50%',
        'margin-left':trangle_margin_left,
        'border-width':'5px',
        'border-style':'solid',
        'border-color':f'{backgroundColor} transparent transparent transparent',
        }
    #排版和包裝
    span_tip_elt<=span_trangle_elt
    div_tip=DIV(elt+span_tip_elt)
    #設定顯示文字框的模式
    div_tip.style={
            'position':'relative',
            'display':'inline-block',
        }
    #定義顯示或隱藏動作
    def switch_tip(ev):
        span_tip_elt=ev.currentTarget.select('span')[0]
        if ev.type in show_ev_list:
            span_tip_elt.style.visibility="visible"
        elif ev.type in hide_ev_list:
            span_tip_elt.style.visibility="hidden"
    #根據輸入的事件列表綁定DIV元素
    for ev in show_ev_list+hide_ev_list:
        div_tip.bind(ev,switch_tip)

    return div_tip

AddStyle("""
    .hidden{
        display:none;
    }

""")

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

#定義功能函數，從HTML原始碼抓取表符網址列表 (使用Brython技術萃取)
def getEmojiUrlListFromHtml(html_str):
    div_elt=DIV()
    div_elt.innerHTML=html_str
    img_emoji_elt_list=[img_elt for img_elt in div_elt.select('img') if "https://emos.plurk.com/" in img_elt.src]
    emoji_url_list=list(set(img_elt.src for img_elt in img_emoji_elt_list))
    div_elt.clear()
    return emoji_url_list

#定義功能函數，從HTML原始碼抓取表符網址列表 (使用字串擷取) (已棄用)
def getEmojiUrlListFromHtml_old(html_str):
    sandWord,wichWord='emos.plurk.com/','"'
    emojiUrlList=SandwichWord_list(sandWord,wichWord,html_str)
    emojiUrlList_com=[]
    for emojiUrl in emojiUrlList:
        #不納入重複表符
        if emojiUrl not in emojiUrlList_com:
            #若emojiUrl後方有反斜線就協助去除
            print(emojiUrl)
            if emojiUrl and emojiUrl[-1]=="/":
                emojiUrl=emojiUrl[:-1]
            if any(pic_format in emojiUrl for pic_format in [".bmp",".png",".jpeg",".jpg",".ico"]) and not any(illegal_character in emojiUrl for illegal_character in ["<","*",">","="]):
                emojiUrlList_com.append(emojiUrl)
    return ["https://emos.plurk.com/"+emojiUrl for emojiUrl in emojiUrlList_com]

#擷取表符網址後段id
def EmojiUrlId(emoji_url):
    return emoji_url[emoji_url.rfind('/')+1:emoji_url.rfind('.')]

#定義動作:跳至新增組合表符頁面
def JumpToAddCombindEmoji(emoji_url):
    doc['button_bar_add_emoji'].click()
    doc['select_adding_emoji_method'].value="組合表符"
    doc['btn_clean_combind_emoji'].click()
    change_ev=window.Event.new("change")
    doc['select_adding_emoji_method'].dispatchEvent(change_ev)
    focus_ev=window.FocusEvent.new("focus")
    doc['textarea_input_combind_emoji_urls'].dispatchEvent(focus_ev)
    doc['textarea_input_combind_emoji_urls'].style.color="black"
    doc['textarea_input_combind_emoji_urls'].value=f"*{emoji_url}*"

#定義動作:跳至搜尋表符
def JumpToSearchEmoji(input_value):
    doc['button_bar_search_emoji'].click()
    doc['search_tag'].value=input_value
    doc['search_tag_btn'].click()

#定義函數:轉換json為python的dict (for Firebase)
def JSObject_to_PythonDict(json_obj):
    new_dict = {}
    for key in dir(json_obj):
        value = json_obj[key]
        if isinstance(value, str) or isinstance(value, int) or isinstance(value, float) or isinstance(value, list) or isinstance(value, dict) or isinstance(value, tuple) or isinstance(value, set):
            new_dict[key] = value
        else:
            new_dict[key] = JSObject_to_PythonDict(value)
    return new_dict

#定義含文字勾選元素A_INPUTCheckbox，點擊文字也可進行勾選
#attr_dict可設定設置inputCheckbox勾選元素的附帶變數
def A_INPUTCheckbox(item_name,checked=False,attr_dict={"symbol":""},Class=None,id=None):
    #定義SPAN文字被勾選時動作:勾選前方的checkbox
    def do_ckecking(ev):
        if ev.target.tagName!="INPUT":
            input_ckeckbox_elt=ev.currentTarget.select("input")[0]
            input_ckeckbox_elt.click()
    #設置inputCheckbox勾選元素，並選擇性加上Class

    inputCheckbox_elt=INPUT(type="checkbox",checked=checked)
    if Class:
        inputCheckbox_elt.className=Class
    if id:
        inputCheckbox_elt.id=id
    if attr_dict:
        for k,v in attr_dict.items():
            setattr(inputCheckbox_elt,k,v)
    return SPAN(inputCheckbox_elt+SPAN(item_name),style={"cursor":"pointer"}).bind('click',do_ckecking)

#自表符網址中獲取表符圖片的長寬像素長度
def GetEmojiWidthAndHeight(emoji_url):
    w,h=None,None
    if ("_w" in emoji_url) and ("_h" in emoji_url):
        w=int(emoji_url[emoji_url.index("_w")+2:emoji_url.index("_h")])
        h=int(emoji_url[emoji_url.index("_h")+2:emoji_url.rfind(".")])
    return w,h

#按下第一個頁籤刷新頁面(會有多餘頁籤按鈕問題，目前找不到方法使用此函式)
def RefreshSreachResultOnFristPage():
    btn_page_elt_list=doc['emoji_page_btns'].select('button')
    if btn_page_elt_list:
        btn_page_elt_list[0].click()