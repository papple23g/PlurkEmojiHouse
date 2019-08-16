"""
負責處理搜尋請求相關的函式
"""

#定義頁籤按鈕，在生成時吸收(附加屬性)搜尋關鍵字
def BUTTON_emijiPage_elt(num_of_emoji_page,search_tag_str):
    #定義頁籤按鈕被按下時，套用被按下的樣式，並解除其它為未被按下的頁籤樣式
    def BUTTONEmijiPageEltPressed(ev):
        btn_elt_list=doc['emoji_page_btns'].select('button')
        for btn_elt in btn_elt_list:
            btn_elt.classList.remove("emoji_page_btn_press")
        ev.currentTarget.classList.add("emoji_page_btn_press")

    btn_elt=BUTTON(num_of_emoji_page,Class="emoji_page_btn")
    btn_elt.search_tag=search_tag_str
    btn_elt.bind("click",SendRequest_searchEmoji)
    btn_elt.bind("click",BUTTONEmijiPageEltPressed)
    return btn_elt
AddStyle('''
    .emoji_page_btn_press{
        background-color:#aaa;
    }
''')


#*搜尋表符並顯示結果*
def SendRequest_searchEmoji(ev):
    page=0 #頁籤預設為第一頁
    request_type=None #搜尋方式變數

    #--根據不同的搜尋方式抓取欲搜尋的關鍵字--
    #使用搜尋欄時，抓取搜尋框的文字
    if ev.currentTarget.id=="search_tag_btn":
        search_tag_str=doc['search_tag'].value.strip()
        request_type="search emoji by input tag"
    #使用[全部顯示]時，關鍵字為空白並清空搜尋欄和相似標籤結果
    elif ev.currentTarget.id=="show_all_emoji_btn":
        search_tag_str=""
        doc['search_tag'].value=""
        doc['search_tag_result'].clear()
        request_type="search emoji by click show all"
    #使用頁籤按鈕時，從按鈕物件上提取關鍵字，並抓取欲搜尋的頁次數字
    elif ev.currentTarget.className=="emoji_page_btn":
        btn_elt=ev.currentTarget
        search_tag_str=btn_elt.search_tag
        page=int(btn_elt.text)-1
        request_type="search emoji by click page button"
    #使用標籤搜尋時，從標籤物件上提取關鍵字
    elif ev.currentTarget.className=="tag_btn":
        search_tag_str=ev.currentTarget.text
        request_type="search emoji by click tag in emoji tag list"
        #點擊一下[搜尋表符]頁籤，確保出現在搜尋結果頁面(新增表符點擊標籤時會跳至搜尋表符頁面)
        doc['button_bar_search_emoji'].click()
    #使用上方標籤搜尋結果區塊的標籤搜尋時
    elif ev.currentTarget.className=="search_result_tag_btn":
        search_tag_str=ev.currentTarget.select(".search_result_tag_btn_text")[0].text
        request_type="search emoji by click tag in search tag result"

    #定義動作:等待搜尋結果中，顯示提示訊息
    def OnLoading_searchEmoji(res):
        #清空表符結果區塊以便顯示新的結果
        doc['emoji_result_table'].clear()
        doc['emoji_result_table']<=P("搜尋表符中...")

    #定義動作:顯示表符搜尋結果TABLE
    def OnComplete_searchEmoji(res):
        #清空表符結果區塊以便顯示新的結果
        doc['emoji_result_table'].clear()
        #沒有找到表符的情況
        if res.text[0]==u'沒':
            doc['emoji_result_table']<=P(res.text)
        #有找到表符的情況
        else:
            doc['emoji_result_table']<=TABLE_emojiReslut(res)
            #若為網址新增表符動作，則清空搜尋欄文字
            if request_type=="search or add emoji by input url":
                doc['search_tag'].value=""

    #若為表符網址，則設定url為搜尋或新增表符
    if "s.plurk.com" in search_tag_str:
        request_type="search or add emoji by input url"
        emoji_url=Correcting_emojiUrl(search_tag_str)
    
    #獲取使用者uid (若尚未登入則為None)
    user_uid=window.firebase.auth().currentUser.uid if window.firebase.auth().currentUser else None

    if user_uid and doc['checkbox_showCollectEmojis'].checked:
        search_tag_str+=f",__collectorUsers__{user_uid}"

    #根據不同搜尋方式設定request
    if request_type=="search or add emoji by input url":
        url=f'/PlurkEmojiHouse/search_by_url?search_url={emoji_url}&user_uid={user_uid}'
    else:
        url=f'/PlurkEmojiHouse/search_by_tag?search_tag={search_tag_str}&page={page}&user_uid={user_uid}'
    req = ajax.ajax()
    req.bind('complete',OnComplete_searchEmoji)
    req.bind('loading',OnLoading_searchEmoji)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

    #若不是以頁籤進行搜尋，則進行生成頁籤按鈕請求處理
    if request_type!="search emoji by click page button":
        SendRequest_insertEmojiPageBtn(search_tag_str)
    
    #若是輸入標籤搜尋或點擊標籤搜尋，就搜尋相似的標籤 (排除空白關鍵字和辨識使用者是否收藏的標籤)
    if search_tag_str.strip() and ("__collectorUsers__" not in search_tag_str):
        if request_type in ["search emoji by input tag","search emoji by click tag in emoji tag list"]:
            SendRequest_searchTags(search_tag_str)

#定義請求動作:顯示表符搜尋結果的頁籤按鈕
def SendRequest_insertEmojiPageBtn(search_tag_str):
    #定義動作:顯示表符搜尋結果的頁籤按鈕
    def OnComplete_insertEmojiPageBtn(res):
        num_of_emoji_page_btn=int(res.text)
        for num_of_emoji_page in range(1,num_of_emoji_page_btn+1):
            doc['emoji_page_btns']<=BUTTON_emijiPage_elt(num_of_emoji_page,search_tag_str)
        #預設第一個頁籤按鈕為按下的狀態(僅會在「搜尋表符」子頁面下發揮作用)
        if doc['emoji_page_btns'].select("#emoji_page_btns > button:nth-child(1)"):
            doc['emoji_page_btns'].select("#emoji_page_btns > button:nth-child(1)")[0].classList.add('emoji_page_btn_press')
    url=f'/PlurkEmojiHouse/numOfEmojiPageBtn?search_tag={search_tag_str}'
    req = ajax.ajax()
    req.bind('complete',OnComplete_insertEmojiPageBtn)
    req.bind('loading',lambda ev:doc['emoji_page_btns'].clear()) #讀取時清空頁籤按鈕區塊
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

#定義送出請求動作:其他搜尋關鍵字的情況則同時搜尋相似標籤
def SendRequest_searchTags(search_tag_str):
    #定義完成搜尋標籤時的動作
    def OnComplete_searchTags(res):
        #獲取符合搜尋的標籤和被使用次數的兩個串列
        tag_list,num_of_tagged_list=json.loads(res.text)
        #根據被標籤次數排序內容:先倆倆綁定，排序，再解除綁定
        ziped_tag_data_list=zip(tag_list,num_of_tagged_list)
        ziped_tag_data_list=sorted(ziped_tag_data_list,key=lambda x:x[1],reverse=True)
        tag_list,num_of_tagged_list=zip(*ziped_tag_data_list) if ziped_tag_data_list else ([],)
        #清除"搜尋標籤中..."訊息
        doc['search_tag_result'].clear()
        #依序置入標籤SPAN
        for i_tag in range(len(tag_list)):
            tag_str=tag_list[i_tag]
            num_of_tagged=num_of_tagged_list[i_tag]
            #顯示包含關鍵字的標籤和備標註的次數
            span_search_result_tag_btn_elt=SPAN(
                SPAN(tag_str,Class="search_result_tag_btn_text")+SPAN(" "+str(num_of_tagged),style={'color':'#ddd'}),
                Class="search_result_tag_btn",
            )
            #綁定點擊後進行搜尋表符動作
            span_search_result_tag_btn_elt.bind('click',SendRequest_searchEmoji)
            doc['search_tag_result']<=span_search_result_tag_btn_elt+SPAN(" ")
    
    #清空之前的搜尋結果
    doc['search_tag_result'].clear()
    req = ajax.ajax()
    req.bind('complete',OnComplete_searchTags)
    url='/PlurkEmojiHouse/search_tags?search_tag=%s' %(search_tag_str)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

#定義送出請求動作:新增表符
def SendRequest_addTag(ev):
    #完成送出時的動作:顯示已增加的標籤
    def OnComplete_addTag(res):
        #獲取表符id
        emoji_id=res.text
        #獲取新增表符中提示訊息SPAN元素
        span_msg_of_adding_tag_elt=doc[f"msg_of_adding_tag_{emoji_id}"]
        #獲取標籤列TD元素
        td_tag_list_elt=ParentElt(span_msg_of_adding_tag_elt,"TD")
        div_tag_list_elt=td_tag_list_elt.select(".div_span_tag_list")[0]
        #若標籤列表DIV元素被影藏，就點及切換純文字按鈕圖示元素切換回來
        if "hidden" in div_tag_list_elt.className:
            #獲取切換純文字按鈕圖示元素
            icon_change_tag_list_to_str_elt=ParentElt(td_tag_list_elt,"TR").nextSibling.select("i.change_tag_list_to_str")[0]
            #點擊切換純文字按鈕圖示元素
            icon_change_tag_list_to_str_elt.click()

        #獲取欲新增的標籤字串list(自新增表符中提示訊息SPAN元素)
        new_tags_with_comma_str=span_msg_of_adding_tag_elt.new_tags_with_comma_str
        new_tags_list=[tag.strip() for tag in new_tags_with_comma_str.split(",")]
        #獲取已有的標籤字串list
        old_tag_list=[span_elt.text for span_elt in div_tag_list_elt.select('.tag_btn')]
        #對於舊的沒有的新的標籤，新增SPAN_tag元素至TD元素中，並加入間隔SPAN
        for new_tags in [tag for tag in new_tags_list if (tag not in old_tag_list)]:
            div_tag_list_elt<=SPAN_tag(new_tags)+SPAN(" ")
        #刪除新增表符中提示訊息SPAN元素
        span_msg_of_adding_tag_elt.remove()
        #清空新增標籤INPUT元素內的文字
        input_new_tags_text_elt=ParentElt(td_tag_list_elt,"TR").nextSibling.select('input.adding_emoji_tag')[0]
        input_new_tags_text_elt.value=""

    #獲取當列IMG表符元素的id(自新增標籤按鈕)
    emoji_id=int(ev.currentTarget.emoji_id)
    #獲取輸入標籤的字串
    input_new_tags_text_elt=ParentElt(ev.currentTarget,"TR").select('input')[0]
    #若尚未輸入標籤，就不動作
    if input_new_tags_text_elt.value.strip()=="":
        return
    new_tags_with_comma_str=input_new_tags_text_elt.value
    #獲取表符標籤列DIV元素
    div_span_tag_list_elt=ParentElt(ev.currentTarget,"TR").previousSibling.select('.div_span_tag_list')[0]
    #置入"新增標籤中..."訊息，並附上emoji_id以供辨識
    span_msg_of_adding_tag_elt=SPAN(
        "新增標籤中...",
        Class=".msg_of_adding_tag",
        id=f"msg_of_adding_tag_{emoji_id}"
    )
    #將新增標籤中訊息SAPN元素附上標籤文字訊息，並置入標籤列中
    span_msg_of_adding_tag_elt.new_tags_with_comma_str=new_tags_with_comma_str
    div_span_tag_list_elt<=span_msg_of_adding_tag_elt

    if new_tags_with_comma_str:
        req = ajax.ajax()
        req.bind('complete',OnComplete_addTag)
        url=f'/PlurkEmojiHouse/emoji_add_tag?id={emoji_id}&add_tag_str={new_tags_with_comma_str}'
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()
    else:
        pass

#定義送出請求動作:新增表符
def SendRequest_collectEmoji(ev,user_uid):
    #完成送出時的動作
    def OnComplete_collectEmoji(res):
        #alert("收藏成功!")
        pass

    #獲取當列IMG表符元素的id
    emoji_id=int(ev.currentTarget.emoji_id)
    collect_tag=f"__collectorUsers__{user_uid}"
    
    req = ajax.ajax()
    req.bind('complete',OnComplete_collectEmoji)
    url=f'/PlurkEmojiHouse/emoji_add_tag?id={emoji_id}&add_tag_str={collect_tag}'
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

def SendRequest_removeCollectEmoji(ev,user_uid):
    #完成送出時的動作
    def OnComplete_removeCollectEmoji(res):
        #alert("已移除收藏!")
        pass

    #獲取當列IMG表符元素的id
    emoji_id=int(ev.currentTarget.emoji_id)
    collect_tag=f"__collectorUsers__{user_uid}"
    
    req = ajax.ajax()
    req.bind('complete',OnComplete_removeCollectEmoji)
    url=f'/PlurkEmojiHouse/delete_tag?emoji_id={emoji_id}&tag_name={collect_tag}'
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()



#定義請求:刪除標籤
def SendRequest_DeleteTag(ev):
    ev.preventDefault() #防止出現右鍵選單
    #獲取要刪除標籤的名稱
    tag_name=ev.currentTarget.text
    #從TD標籤列表中獲取表符id
    emoji_id_str=str(ParentElt(ev.currentTarget,"TD").emoji_id)
    #設置確認刪除的跳出視窗
    confirm_box=("確定要刪除 [{}] 這個標籤嗎?".format(tag_name))
    going_to_del_tag=window.confirm(confirm_box)
    #若確定要刪除標籤
    if going_to_del_tag:
        #送出刪除請求
        req = ajax.ajax()
        url='/PlurkEmojiHouse/delete_tag?emoji_id='+emoji_id_str+'&tag_name='+tag_name
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()

        #刪除SPAN標籤元素和SPAN間格空白元素
        ev.currentTarget.remove()
        if ev.currentTarget.previousSibling:
            ev.currentTarget.previousSibling.remove()

#定義請求:新增表符
adding_emoji_type="" #全域變數:新增表符的方式
def SendRequest_addEmoji(ev):
    #獲取輸入欄input(或textarea)元素
    input_elt=ev.currentTarget.previousSibling
    #若文字欄內容空白，就不發動新增動作
    if input_elt.value.strip()=="":
        return

    #清除之前的新增結果
    doc['div_show_adding_emoji_result_table_area'].clear()
    #全域變數:新增表符的方式
    global adding_emoji_type
    for msg_string_elt in doc.select('.msg_string'):
        msg_string_elt.classList.add("hidden")
    #定義等待新增表符時的動作
    def OnLoading_addEmoji(res):
        #顯示訊息:新增表符中
        doc['adding_emoji_msg'].classList.remove("hidden")
    #定義完成新增表符後動作
    def OnComplete_addEmoji(res):
        #關閉訊息:新增表符中
        doc['adding_emoji_msg'].classList.add("hidden")
        #有接收到訊息
        if res.status==200 or res.status==0:
            #回傳失敗時
            if res.text[0]==u'沒':
                doc["div_show_adding_emoji_result_table_area"]<=res.text
            #成功收到表符字典資料時
            else:
                #新增獨立Table
                doc['div_show_adding_emoji_result_table_area']<=TABLE_emojiReslut(res)
        #未接收到訊息或錯誤
        else:
            doc["div_show_adding_emoji_result_table_area"].html = "error "+res.text

    #定義動作:顯示錯誤提示-非法網址
    def ShowEmojiUrlErrorMsg():
        doc['incorrect_emoji_url_msg'].classList.remove("hidden")

    #若為輸入單一表符圖片網址
    if input_elt.id=="input_input_emoji_url_to_add_emoji_elt":
        #更正表符網址後新增
        emoji_url=input_elt.value
        emoji_url=Correcting_emojiUrl(emoji_url)
        if emoji_url:
            url=f'/PlurkEmojiHouse/search_by_url?search_url={emoji_url}'
            req = ajax.ajax()
            req.bind('complete',OnComplete_addEmoji)
            req.bind('loading',OnLoading_addEmoji)
            req.open('GET',url,True)
            req.set_header('content-type','application/x-www-form-urlencoded')
            req.send()
        #若為非法網址則顯示錯誤
        else:
            ShowEmojiUrlErrorMsg()
    #若為輸入噗文網址
    elif input_elt.id=="input_input_plurk_url_to_add_emoji_elt":
        plurk_url=input_elt.value
        SendRequest_PlurkUrlToHtml(plurk_url)
    #若為輸入HTML
    elif input_elt.id=="textarea_input_html_to_add_emoji_elt":
        #獲取輸入欄textarea元素
        html_str=input_elt.value
        #獲取表符列表
        emoji_url_list=getEmojiUrlListFromHtml(html_str)
        #顯示HTML裡面包含的所有表符以供選取
        doc['div_show_adding_emoji_result_table_area']<=DIV_emojiUrlList_to_divImgList(emoji_url_list)
    
    #清空文字欄
    input_elt.value=""

#定義動作:轉換噗文網址為HTML
def SendRequest_PlurkUrlToHtml(plurk_url):
    #清除之前的新增結果
    doc['div_show_adding_emoji_result_table_area'].clear()
    #定義等待新增表符時的動作
    def OnLoading_PlurkUrlToHtml(res):
        #顯示訊息:新增表符中
        doc['adding_emoji_msg'].classList.remove("hidden")
    #定義完成時新增表符時的動作
    def OnComplete_PlurkUrlToHtml(res):
        #關閉訊息:新增表符中
        doc['adding_emoji_msg'].classList.add("hidden")
        if res.text=="":
            return
        #有接收到訊息
        if res.status==200 or res.status==0:
            #回傳失敗時
            if res.text[0]==u'沒':
                doc["div_show_adding_emoji_result_table_area"]<=res.text
            #顯示HTML裡面包含的所有表符以供選取
            else:
                html_str=res.text
                emoji_url_list=getEmojiUrlListFromHtml(html_str)
                doc['div_show_adding_emoji_result_table_area']<=DIV_emojiUrlList_to_divImgList(emoji_url_list)
        #未接收到訊息或錯誤
        else:
            doc["div_show_adding_emoji_result_table_area"].html = "error "+res.text

    url=f'/PlurkEmojiHouse/PlurkUrlHtml?plurk_url={plurk_url}'
    req = ajax.ajax()
    req.bind('loading',OnLoading_PlurkUrlToHtml)
    req.bind('complete',OnComplete_PlurkUrlToHtml)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()


#定義動作:全選，選取尚未選取的html表符
def SelectAllHtmlEmoji(ev):
    for unselected_htmlEmoji_elt in [elt for elt in doc['html_emoji_container'].select('div.html_emoji') if ('selected_html_emoji' not in elt.className)]:
        unselected_htmlEmoji_elt.classList.add("selected_html_emoji")

#定義動作:取消全選，取消選取已經選取的html表符
def UnselectAllHtmlEmoji(ev):
    for selected_htmlEmoji_elt in doc['html_emoji_container'].select('.selected_html_emoji'):
        selected_htmlEmoji_elt.classList.remove("selected_html_emoji")

def SendConfirmSelectedHtmlEmojiToAdd(ev):
    selected_imgHtmlEmoji_elt_list=doc['html_emoji_container'].select('.selected_html_emoji img')
    selected_imgHtmlEmoji_url_list=[elt.src for elt in selected_imgHtmlEmoji_elt_list]
    emoji_url_list_str=",".join(selected_imgHtmlEmoji_url_list)
    #有選取表符時，才進行批量新增表符
    if selected_imgHtmlEmoji_url_list:
        SendRequest_addEmojiList(emoji_url_list_str)
    #未選取表符時，就不進行動作
    else:
        pass

#處理表符網址串列變成可視區塊列表，可選取和取消選取表符，附帶功能按鈕
def DIV_emojiUrlList_to_divImgList(emoji_url_list):
    div_elt=DIV(id="html_emoji_container")
    div_emojiBlocks_elt=DIV()
    for emoji_url in emoji_url_list:
        img=IMG(src=emoji_url)
        div_emojiBlocks_elt<=DIV(
            DIV(
                img,
                Class="html_emoji",
            ).bind('click',lambda ev:ev.currentTarget.classList.toggle("selected_html_emoji")),
            Class="html_emoji_block"       
        )
    btn1=BUTTON("全選",id="btn_select_all").bind('click',SelectAllHtmlEmoji)
    btn2=BUTTON("全不選",id="btn_unselect_all").bind('click',UnselectAllHtmlEmoji)
    btn3=BUTTON("確定新增",id="btn_send_confirm_selected").bind('click',SendConfirmSelectedHtmlEmojiToAdd)
    div_elt<=btn1+btn2+div_emojiBlocks_elt+DIV(btn3,style={"clear":"both"})
    if emoji_url_list:
        return div_elt
    else:
        return P("此原始碼未包含表符")
AddStyle("""
    div.html_emoji{
        width: 54px;
        height: 54px;
        cursor:pointer;
    }
    div.html_emoji_block{
        width: 56px;
        height: 56px;
        float: left;
        margin-top: 0px;
    }
    div.html_emoji:hover{
        border: 3px yellow solid;
    }
    .selected_html_emoji{
        border: 3px blue solid;
    }
    div.html_emoji.selected_html_emoji:hover{
        border: 3px #3bca02 solid;
    }

""")


#XX#定義送出請求，一次增加所有被列出所選表符的標籤
def send_requset_adding_tag_to_all_emoji(ev):
    if (ev.type=="keyup" and ev.keyCode==13) or (ev.type=="click"):
        emoji_id_str_for_add_list=[img_emoji_elt.id[len("emoji_img"):] for img_emoji_elt in doc['div_emoji_list_from_html'].select('.emoji_pic')]
        emoji_id_str_for_add_list_str=','.join(emoji_id_str_for_add_list)
        tag_list_str=doc['input_adding_tag_to_all_emoji'].value
        req = ajax.ajax()
        req.bind('loading',on_loading_adding_tag_to_all_emoji)
        req.bind('complete',on_complete_adding_tag_to_all_emoji)
        url=f'/PlurkEmojiHouse/emoji_list_add_tag?emoji_id_str_for_add_list_str={emoji_id_str_for_add_list_str}&tag_list_str={tag_list_str}'
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()
    else:
        pass

#定義送出請求:批量新增標籤
def SendRequest_addTagOnAllEmojiAtOnce(ev):
    #獲取批量增加的標籤內容
    new_tags_with_comma_str=doc['input_add_tag_on_all_emoji_at_once'].value
    #獲取所有新增標籤文字框元素列表
    input_addTag_elt_list=doc['div_show_adding_emoji_result_table_area'].select('input.adding_emoji_tag')
    #獲取所有新增標籤按鍵元素列表
    btn_addTag_elt_list=doc['div_show_adding_emoji_result_table_area'].select('.btn_add_tag')
    #從新增標籤按鍵元素上獲取對應的表符id
    emoji_id_list=[str(btn_addTag_elt.emoji_id) for btn_addTag_elt in btn_addTag_elt_list]
    emoji_id_list_str=','.join(emoji_id_list)

    def OnComplete_addTagOnAllEmojiAtOnce(res):
        #移除所有"新增表符中..."訊息
        span_msg_of_adding_tag_elt_list=doc['div_show_adding_emoji_result_table_area'].select('.msg_of_adding_tag')
        for span_msg_of_adding_tag_elt in span_msg_of_adding_tag_elt_list:
            span_msg_of_adding_tag_elt.remove()

        #獲取欲新增的標籤字串list(自新增表符中提示訊息SPAN元素)
        new_tags_with_comma_str=doc['btn_add_tag_on_all_emoji_at_once'].new_tags_with_comma_str
        new_tags_list=[tag.strip() for tag in new_tags_with_comma_str.split(",")]

        #批次處理每個標籤列DIV元素
        div_tag_list_elt_list=doc['div_show_adding_emoji_result_table_area'].select(".div_span_tag_list")
        for div_tag_list_elt in div_tag_list_elt_list:
            #若標籤列表DIV元素被影藏，就點及切換純文字按鈕圖示元素切換回來
            if "hidden" in div_tag_list_elt.className:
                #獲取切換純文字按鈕圖示元素
                icon_change_tag_list_to_str_elt=ParentElt(div_tag_list_elt,"TR").nextSibling.select("i.change_tag_list_to_str")[0]
                #點擊切換純文字按鈕圖示元素
                icon_change_tag_list_to_str_elt.click()

            #補齊SPAN_TAG元素
            #獲取已有的標籤字串list
            old_tag_list=[span_elt.text for span_elt in div_tag_list_elt.select('.tag_btn')]
            #對於舊的沒有的新的標籤，新增SPAN_tag元素至TD元素中，並加入間隔SPAN
            for new_tags in [tag for tag in new_tags_list if (tag not in old_tag_list)]:
                div_tag_list_elt<=SPAN_tag(new_tags)+SPAN(" ")

        #清空批量新增標籤INPUT文字框內容
        doc['input_add_tag_on_all_emoji_at_once'].value=""
        
    
    #在每個標籤列DIV區塊中顯示"新增表符中..."訊息
    div_span_tag_list_elt_list=doc['div_show_adding_emoji_result_table_area'].select('.div_span_tag_list')
    for div_span_tag_list_elt in div_span_tag_list_elt_list:
        div_span_tag_list_elt<=SPAN("新增表符中...",Class="msg_of_adding_tag")

    #在批量新增按鍵元素上傳遞標籤內容
    ev.currentTarget.new_tags_with_comma_str=new_tags_with_comma_str

    req = ajax.ajax()
    req.bind('complete',OnComplete_addTagOnAllEmojiAtOnce)
    url=f'/PlurkEmojiHouse/emoji_list_add_tag?emoji_id_str_for_add_list_str={emoji_id_list_str}&tag_list_str={new_tags_with_comma_str}'
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()


#定義請求:新增表符列表
def SendRequest_addEmojiList(emoji_url_list_str,do_clean_previous_area=True):
    #清除之前的新增結果
    if do_clean_previous_area:
        doc['div_show_adding_emoji_result_table_area'].clear()
    #定義按下Enter送出新增批量標籤
    def pressEnterToSend(ev):
        #在ev有附加屬性key時才執行(避免出現錯誤)
        if hasattr(ev, 'key'):
            if ev.key=="Enter":
                doc['btn_add_tag_on_all_emoji_at_once'].click()
    #設置針對新的表符批量新增標籤的DIV_INPUT_BUTTON元素
    def DIV_addTagOnAllEmojiAtOnce():
        div_elt=DIV(style={"margin-bottom":"8px"})
        div_elt<=SPAN("全部新增標籤: ")
        div_elt<=INPUT(
            id="input_add_tag_on_all_emoji_at_once",
            Class="input_url_elt",
        ).bind("keydown",pressEnterToSend)
        div_elt<=BUTTON(
            "新增",
            id="btn_add_tag_on_all_emoji_at_once",
        ).bind("click",SendRequest_addTagOnAllEmojiAtOnce)
        return div_elt
    #定義等待新增表符時的動作
    def OnLoading_addEmojiList(res):
        #顯示訊息:新增表符中
        doc['adding_emoji_msg'].classList.remove("hidden")
    #定義完成時新增表符時的動作
    def OnComplete_addEmojiList(res):
        #關閉訊息:新增表符中
        doc['adding_emoji_msg'].classList.add("hidden")
        #有接收到訊息
        if res.status==200 or res.status==0:
            #回傳失敗時
            if res.text[0]==u'沒':
                doc["div_show_adding_emoji_result_table_area"]<=res.text
            #成功收到表符字典資料時
            else:
                #置入批量新增標籤DIV區塊
                doc['div_show_adding_emoji_result_table_area']<=DIV_addTagOnAllEmojiAtOnce()
                #置入獨立Table
                doc['div_show_adding_emoji_result_table_area']<=TABLE_emojiReslut(res)
        #未接收到訊息或錯誤
        else:
            doc["div_show_adding_emoji_result_table_area"].html = "error "+res.text

    url=f'/PlurkEmojiHouse/search_by_uuu?search_url_list={emoji_url_list_str}'
    req = ajax.ajax()
    req.bind('loading',OnLoading_addEmojiList)
    req.bind('complete',OnComplete_addEmojiList)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

##定義請求:新增組合表符
def SendRequest_addCombindEmoji(ev):

    #定義動作:複製組合表符網址
    def doCopyCombindEmojiUrl(ev):
        CopyTextToClipborad(ev.currentTarget.combind_url)
        alert(f"複製成功")

    #定義完成時，顯示該組合表符中的表符列表的標籤Table
    def OnComplete_addCombindEmoji(res):
        #新增成功時
        if res.status==200 or res.status==0:
            emoji_url_set=json.loads(res.text)
            emoji_url_list_str=",".join(emoji_url_set)
            #顯示(或者新增)各表符的列表，以便新增表符標籤，其中不要清空之前的顯示組合表符結果
            SendRequest_addEmojiList(emoji_url_list_str,do_clean_previous_area=False)
            #讓新增新增組合表符的按鍵變成複製表符功能，並恢復按鍵作用
            doc['btn_add_combind_emoji'].text="複製組合表符網址"
            doc['btn_add_combind_emoji'].disabled=False
            doc['btn_add_combind_emoji'].unbind("click")
            doc['btn_add_combind_emoji'].bind("click",doCopyCombindEmojiUrl)
        #未接收到訊息或錯誤時
        else:
            doc["div_show_adding_emoji_result_table_area"].html = "error "+res.text

    #獲取組合表符網址
    btn_add_combind_emoji_elt=ev.currentTarget
    combind_url=btn_add_combind_emoji_elt.combind_url

    #轉換斷行符號為「|」符號(確保正確傳送資料)
    combind_url_with_vertical=combind_url.replace("\n","|")
    
    #傳送請求
    url=f'/PlurkEmojiHouse/AddCombindEmoji?combind_url={combind_url_with_vertical}'
    req = ajax.ajax()
    req.bind('complete',OnComplete_addCombindEmoji)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

    #讓新增新增組合表符的按鍵顯示等待提示，並暫停按鍵作用
    doc['btn_add_combind_emoji'].text="新增中..."
    doc['btn_add_combind_emoji'].disabled=True


#定義請求:刪除組合表符
def SendRequest_DeleteCombindEmoji(combind_url,btn_delete_combind_emoji_elt):

    #轉換斷行符號為「|」符號(確保正確傳送資料)
    combind_url_with_vertical=combind_url.replace("\n","|")

    #定義完成刪除組合表符時，跳出提示並刪除對應TR元素
    def OnComplete_DeleteCombindEmoji(res):
        #完成搜尋時
        if res.status==200 or res.status==0:
            alert("刪除成功")
            tr_combind_emoji_elt=ParentElt(btn_delete_combind_emoji_elt,"TR")
            tr_combind_emoji_elt.remove()
            doc['btn_back'].do_delete_combind_url_list.append(combind_url_with_vertical)
        else:
            pass

    #傳送請求
    url=f'/PlurkEmojiHouse/DeleteCombindEmoji?combind_url={combind_url_with_vertical}'
    req = ajax.ajax()
    req.bind('complete',OnComplete_DeleteCombindEmoji)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

#定義請求:搜尋組合表符
def SendRequest_SearchCombindEmoji(emoji_url,combind_emoji_btn_elt):

    #定義完成搜尋組合表符時，將組表符icon染色
    def OnComplete_SearchCombindEmoji(res):
        #完成搜尋時
        if res.status==200 or res.status==0:
            combind_url_list=json.loads(res.text)
            if combind_url_list:
                combind_emoji_btn_elt.classList.add("has_combind_emoji")
                combind_emoji_btn_elt.combind_url_list=combind_url_list
            else:
                pass

    #傳送請求
    url=f'/PlurkEmojiHouse/SearchCombindEmoji?emoji_url={emoji_url}'
    req = ajax.ajax()
    req.bind('complete',OnComplete_SearchCombindEmoji)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()





#定義Firebase請求:讀取瀏覽人數資料並且顯示出來
def ShowAndUpdateWebSiteViews():

    #定義動作:顯示瀏覽人數至本站Header
    def ShowWebSiteViews(webSiteViews):
        doc['span_website_views'].text=f'{webSiteViews:,}'

    #定義Firebase請求:更新瀏覽人數資料
    def UpdateWebSiteViews(data_dict,path):
        database_ref=database.ref(path)
        database_ref.update(data_dict)
        print("已新增:")##
        log(data_dict)##

    path="PlurkEmojiHouse"
    #定義完成讀取後的動作
    def gotData(data):
        data_dict=JSObject_to_PythonDict(data.toJSON())
        webSiteViews=data_dict['WebSiteViews']
        print(webSiteViews)
        #增加瀏覽量並更新瀏覽人數資料
        webSiteViews+=1
        data_dict['WebSiteViews']=webSiteViews
        UpdateWebSiteViews(data_dict,path)
        #顯示瀏覽人數至本站Header
        ShowWebSiteViews(webSiteViews)
    #定義完成讀取後的動作
    def errData(err):
        log("ERROR!")
        log(err)

    database_ref=database.ref(path)
    database_ref.once("value",gotData,errData)
