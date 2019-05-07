"""
負責基本函式或共同的函式
"""

from browser import window,doc,ajax,alert,bind,timer
from browser.html import *
import json
import copy

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

#定義動作:驗證和更正表符網址
def Correcting_emojiUrl(emoji_url):
    if ("s.plurk.com" in emoji_url) and (emoji_url.count(".")==3):
        request_type="search or add emoji by input url"
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

#定義功能函數，從HTML原始碼抓取表符網址列表
def getEmojiUrlListFromHtml(html_str):
    sandWord,wichWord='emos.plurk.com/','"'
    emojiUrlList=SandwichWord_list(sandWord,wichWord,html_str)
    emojiUrlList_com=[]
    for emojiUrl in emojiUrlList:
        #不納入重複表符
        if emojiUrl not in emojiUrlList_com:
            emojiUrlList_com.append(emojiUrl)
    return ["https://emos.plurk.com/"+emojiUrl for emojiUrl in emojiUrlList_com]