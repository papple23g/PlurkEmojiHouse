"""
負責處理產生表符搜尋結果table的函式
"""

#定義TR表符結果表格標頭元素
def TR_emojiReslut():
    com_tr=TR()
    com_tr<=TH(P("表符"))+TH(P("標籤"+SPAN("　點擊:搜尋　右鍵:刪除"
                                    ,style={'color':'white',
                                            'font-size':'10px',
                                            'text-shadow':'1px 1px 2px #555'})))
    return com_tr

#定義IMG表符圖元素
def IMG_emoji(emoji_url):
    #定義動作:複製表符網址
    show_text_str="複製表符網址"
    show_text_on_click_str="已複製"
    def CopyEmojiUrl(ev):
        CopyTextToClipborad(f"*{emoji_url}*")
        span_tooltiptext=ev.currentTarget.parent.select('.tooltiptext')[0]
        #定義動作:改變提示文字
        def ChangeBackTooltiptext():
            span_tooltiptext.text=show_text_str
            #放回框尖端物體(三角元件)樣式
            span_trangle_elt=SPAN("")
            span_trangle_elt.style={
                'position':'absolute',
                'top':'100%',
                'left':'50%',
                'margin-left':'-50px',
                'border-width':'5px',
                'border-style':'solid',
                'border-color':'black transparent transparent transparent',
                }
            span_tooltiptext<=span_trangle_elt
        #點擊後，提示文字變成"已複製"，過1秒後變回原本文字
        span_tooltiptext.text=show_text_on_click_str
        timer.set_timeout(ChangeBackTooltiptext,1000)

    #設置IMG表符元素
    img_elt=IMG(src=emoji_url,Class="emoji_pic",id=f"{EmojiUrlId(emoji_url)}")
    img_elt.bind('click',CopyEmojiUrl)
    
    img_elt=DIV_showTipText(img_elt,show_text_str)
    return img_elt
#設定IMG表符圖樣式
AddStyle('''
    .emoji_pic{
        box-shadow:2px 2px 2px gray;
        cursor: pointer;
    }
    .emoji_pic:hover{
        box-shadow:2px 2px 8px black;
    }
    ''')
#定義SPAN標籤元素
def SPAN_tag(tag_str,style=None):
    #製作輸出元素
    com_elt=SPAN(
                SPAN(tag_str),
                style={
                    'text-decoration':'none',
                    'padding-bottom:':'15px'},
                Class="tag_btn"
            )
    #綁定左鍵搜尋(全域功能函數)
    com_elt.bind("click",SendRequest_searchEmoji)
    #綁定右鍵刪除(局域功能函數)
    com_elt.bind('contextmenu',SendRequest_DeleteTag)
    return com_elt
#設定SPAN標籤元素樣式
AddStyle('''
    .tag_btn , .search_result_tag_btn {
        padding: 5px 12px;
        margin-top:10px;
        font-size: 14px;
        font-weight:bold;
        text-align: center;
        cursor: pointer;
        outline: none;
        color: #fff;
        background-color:rgba(50,100,256,0.7);
        border: none;
        border-radius: 15px;
        box-shadow: 2px 2px #ccc;
    }
    .tag_btn:hover, .search_result_tag_btn:hover{
        background-color: rgba(10,200,200,1);
    }
    .tag_btn:active {
        color:#ccc;
        background-color: rgba(10,50,50,1);
    }
    ''')

#定義TD表符結果表格單橫列元素
def TR_emoji(emoji_url,emoji_id,tag_str_list):

    #定義動作:搜尋或新增組表符
    def SearchOrAddCombindEmoji(ev):
        #點擊[搜尋表符]子頁籤，確保正在該子頁面動作
        doc['button_bar_search_emoji'].click()
        #若該子頁面呈現組合表符頁面，就點擊[返回]按鈕
        if doc.select('#btn_back'):
            doc['btn_back'].click()

        combind_emoji_btn_elt=ev.currentTarget
        #若該表符還沒有組合表符，就詢問是否要新增組合表符
        if "has_combind_emoji" not in combind_emoji_btn_elt.classList:
            do_add_combind_emoji=confirm("這個表符還沒有組合表符，要新增組合表符嗎?")
            #若要新增，就跳至新增組合表符頁面
            if do_add_combind_emoji:
                JumpToAddCombindEmoji(combind_emoji_btn_elt.emoji_url)
            #若不要新增，就不動作
            else:
                pass
        #若該表符已經有組合表符，則戰時切換至組合表符結果頁面
        else:
            #隱藏表符TABLE頁面、頁籤DIV元素、標籤搜尋結果區塊DIV元素
            doc['table_emoji_result'].classList.add("hidden")
            doc['emoji_page_btns'].classList.add("hidden")
            doc['search_tag_result'].classList.add("hidden")
            #置入組合表符結果頁面DIV_TABLE元素
            doc['emoji_result_table']<=DIV_CombindEmojiTable(combind_emoji_btn_elt.combind_url_list,combind_emoji_btn_elt.emoji_url)


    #定義表符圖示下方的動作按鈕
    def TD_emoji_action_area(emoji_url,emoji_id,be_collected=None):

        #定義動作:收藏或移除收藏表符
        def AddOrRemoveEmojiAsFavor(ev):
            #若使用者已經登入
            if window.firebase.auth().currentUser:
                user_uid=window.firebase.auth().currentUser.uid

                collect_emoji_btn_elt=ev.currentTarget
                #若表符尚未被收藏，就進行收藏並亮起愛心按鈕
                if "be_collected" not in collect_emoji_btn_elt.classList:
                    #亮起愛心按鈕
                    collect_emoji_btn_elt.classList.add("be_collected")
                    #送出收藏表符的請求
                    SendRequest_collectEmoji(ev,user_uid)
                #若表符已經被收藏，就移除收藏並調暗愛心按鈕
                else:
                    #調暗愛心按鈕
                    collect_emoji_btn_elt.classList.remove("be_collected")
                    SendRequest_removeCollectEmoji(ev,user_uid)
            
            #若使用者尚未登入
            else:
                alert("若要收藏表符，請先登入哦")


        td_elt=TD(Class="emoji_action_area")
        div_elt=DIV()

        #設置在噗浪上搜尋表符icon元素，並置入emoji_id附加參數以利送出收藏請求
        collect_emoji_btn_elt=I(
            Class="emoji_action fas fa-heart",
        ).bind("click",AddOrRemoveEmojiAsFavor)
        collect_emoji_btn_elt.emoji_id=emoji_id
        #若該列表符已被收藏，就調亮愛心按鈕
        if be_collected:
            collect_emoji_btn_elt.classList.add("be_collected")

        #設置搜尋組合表符icon元素
        combind_emoji_btn_elt=I(
            Class=f"emoji_action fas fa-th-large icon_combind_emoji {EmojiUrlId(emoji_url)}",
            title="查看組合表符",
        ).bind("click",SearchOrAddCombindEmoji)

        combind_emoji_btn_elt.emoji_url=emoji_url
        #預定設置附加物件:組合表符網址列表
        combind_emoji_btn_elt.combind_url_list=None

        #送出請求:搜尋還此表符的組合表符，並且會根據結果改變icon的classList
        SendRequest_SearchCombindEmoji(emoji_url,combind_emoji_btn_elt)
        
        #排版
        div_elt<=combind_emoji_btn_elt
        div_elt<=collect_emoji_btn_elt
        td_elt<=div_elt
        return td_elt
    #定義動作:在輸入標籤欄上按下Enter時，點擊新增表符DIV按鈕
    def PressEnterToAddTag(ev):
        if ev.key=="Enter":
            div_button_elt=ev.currentTarget.nextSibling.children[0]
            div_button_elt.click()
    #定義TR新增標籤功能欄元素
    def TD_function():
        td_elt=TD(
            style={
                'height':'30px',
                'padding-left':'10px',
                'padding-top':'5px',
                'padding-bottom':'5px'
                },
            Class="emoji_action_area",
            )
        #設置容器
        div_elt=DIV(style={'float':'left','width':'100%',})
        #設置INPUT輸入元素
        div_elt<=INPUT(
            type='text',
            Class="adding_emoji_tag",
            title="新增標籤",
        ).bind('keydown',PressEnterToAddTag)
        #設置新增表符按鈕
        def DIV_add_tag_button():
            btn_elt=BUTTON(style={'border':'#aaa 2px solid',
                                'background-color':'#fff',
                                'border-radius':'10px',
                                'float':'left',
                                'margin-left':'5px',
                                'height':'28px',
                                'cursor':'pointer',
                                'width':'20%',
                                'max-width':'66px'}
                        ,Class="btn_add_tag")
            btn_elt.emoji_id=emoji_id
            btn_elt<=SPAN(
                "新增",
                style={'color':'#aaa'},
                title="新增標籤",
                )
                       
            btn_elt.bind('click',SendRequest_addTag)
            return btn_elt

        #定義動作:改變SAPN標籤為純文字
        def ChangeTagListToString(ev):
            #套用Class樣式:加深背景
            ev.currentTarget.classList.toggle("icon_pressed")
            #獲取標籤列表DIV區塊
            tr_span_tag_list_elt=ParentElt(ev.currentTarget,"TR").previousSibling
            div_span_tag_list_elt=tr_span_tag_list_elt.select(".div_span_tag_list")[0]
            #獲取標籤列表SPAN串列
            span_tags_elt_list=div_span_tag_list_elt.select(".tag_btn")
            #獲取顯示標籤純文字DIV區塊
            div_tag_list_with_comma_str_area=tr_span_tag_list_elt.select("div.tag_list_with_comma_str_area")[0]
            #生成標籤列表純文字(以","間隔)
            tag_list_with_comma_str=", ".join([span_tags_elt.text for span_tags_elt in span_tags_elt_list])
            #隱藏標籤列表DIV區塊、顯示標籤純文字區塊
            div_span_tag_list_elt.classList.add("hidden")
            div_tag_list_with_comma_str_area.classList.add("hidden")
            #置入(顯示)標籤列表純文字
            div_tag_list_with_comma_str_area.innerHTML=tag_list_with_comma_str
        
        #定義動作:複製標籤列表純文字
        def CopyTagListStr(ev):
            #獲取標籤列表DIV區塊
            div_span_tag_list_elt=ParentElt(ev.currentTarget,"TR").previousSibling.select(".div_span_tag_list")[0]
            #獲取標籤列表SPAN串列
            span_tags_elt_list=div_span_tag_list_elt.select(".tag_btn")
            #生成標籤列表純文字(以","間隔)
            tag_list_with_comma_str=", ".join([span_tags_elt.text for span_tags_elt in span_tags_elt_list])
            #複製標籤列表到剪貼簿
            CopyTextToClipborad(tag_list_with_comma_str)
            #抓取tooltip訊息並替換文字
            div_icon_copy_elt=ParentElt(ev.currentTarget,"DIV")
            div_icon_copy_elt_innerHTML_save=copy.copy(div_icon_copy_elt.innerHTML)
            div_icon_copy_elt.innerHTML=div_icon_copy_elt.innerHTML.replace("複製所有標籤","已複製")
            div_tagListActionIconList=div_icon_copy_elt.parent
            #設置動作:恢復tooltip訊息，包含恢復bind click事件
            def ChangeBackCopyMsg():
                #定義動作:重新生成icon
                def ReplaceIconElt():
                    div_icon_copy_elt.remove()
                    div_tagListActionIconList<=DIV_showTipText(
                        I(Class="tag_list_action far fa-copy copy_tag_list_str").bind("click",CopyTagListStr),
                        "複製所有標籤",
                        tip_margin_left='-100px',
                        trangle_margin_left='30px'
                    )
                div_icon_copy_elt.innerHTML=div_icon_copy_elt.innerHTML.replace("已複製","複製所有標籤")
                #設置一秒後重新生成icon
                timer.set_timeout(ReplaceIconElt,1000)
            #設置一秒後恢復tooltip訊息
            timer.set_timeout(ChangeBackCopyMsg,1000)

        #設置複製標籤列按鈕<i class="far fa-window-maximize"></i>
        def DIV_tagListActionIconList():
            div_elt=DIV(style={'float':'right'})
            div_elt<=I(
                Class="tag_list_action far fa-window-maximize change_tag_list_to_str",
                title="顯示/隱藏純文字標籤"
            ).bind("click",ChangeTagListToString)
            div_elt<=DIV_showTipText(
                I(Class="tag_list_action far fa-copy copy_tag_list_str").bind("click",CopyTagListStr),
                "複製所有標籤",
                tip_margin_left='-100px',
                trangle_margin_left='30px'
            )
            return div_elt
        
        #排版
        td_elt<=div_elt
        div_elt<=DIV_add_tag_button()
        div_elt<=DIV_tagListActionIconList()
        
        return td_elt
    #定義函數，透過emoji_url字串抓取表符的寬和高
    def GetEmojiImg_w_h(emoji_url):
        if ("_w" in emoji_url) and ("_h" in emoji_url) and (emoji_url.count(".")==3):
            w_str=SandwichWord_list('_w','_',emoji_url)[0]
            h_str=SandwichWord_list('_h','.',emoji_url)[0]
            return int(w_str),int(h_str)
        else:
            return 48,48
    #輸出一個置中img表符的td元素
    global thEmoji_width
    w_img,h_img=GetEmojiImg_w_h(emoji_url)
    padding_left_td=(thEmoji_width-w_img)/2

    #設置TD表符圖片元素
    def TD_IMG_emoji():
        td_elt=TD(IMG_emoji(emoji_url),
                    style={'padding-left':f"{padding_left_td}",
                           'vertical-align':'middle',
                           'text-align':'center',
                    })
        return td_elt
    #設置TD標籤列表元素
    td_span_tag_list=TD(
        style={
            'padding':'10px 10px 17px',
            'border-bottom':'1px solid #bbb',
            "line-height":"28px",
        }
    )
    #在TD標籤列表元素設置表符id資訊的附加變數
    td_span_tag_list.emoji_id=emoji_id

    #置入純文字位置
    td_span_tag_list<=DIV(Class="tag_list_with_comma_str_area hidden")

    #在TD標籤列置入SPAN標籤(以逗號為分隔)
    be_collected=False
    div_span_tag_list=DIV(Class="div_span_tag_list")
    for tag_str in tag_str_list.split(","):
        #若tag中含有已被使用者收藏的標記...
        if tag_str=="__be_collected__":
            be_collected=True
        #若表符不為空
        elif tag_str!="":
            div_span_tag_list<=SPAN_tag(tag_str)+SPAN(" ") #設定標籤內容不斷行
    td_span_tag_list<=div_span_tag_list
    #置入等待新增訊息元素
    td_span_tag_list<=SPAN("新增表符中...",Class="msg_of_adding_tag",style={"display":"none"})
    #進行排版
    com_tr=(
        TR(
            TD_IMG_emoji()
            + td_span_tag_list
        )
        +TR(
            TD_emoji_action_area(emoji_url,emoji_id,be_collected=be_collected)
            + TD_function()
        )
    )
    return com_tr
AddStyle('''
    .icon_combind_emoji{
        cursor: pointer;
    }
    .icon_combind_emoji.has_combind_emoji{
        color: #d23c00b5;
        border-color: #d23c0080;
    }
    .fa-heart.be_collected{
        color: #f79be7;
        border-color: #ff77d5;
    }
    .icon_pressed{
        background-color: #ddd;
        color: #aaa !important;
        border-color: #aaa !important;
    }
    input.adding_emoji_tag{
        border: 2px solid rgb(170, 170, 170);
        outline: none;
        border-radius: 20px;
        padding-left: 12px;
        float: left;
        width: 50%;
        max-width: 200px;
    }
    td.emoji_action_area,td.emoji_action_area{
        border-bottom-color: #838de9;
        border-bottom-width: 3px;
    }
    div.btn_add_tag:hover{
        background-color:#ccc;
    }
    div.btn_add_tag:active{
        transform:scale(0.9,0.9);
    }
    div.btn_add_tag:hover>span{
        color:white !important;
    }
    .btn_add_tag span{
        font-weight:bold;
        font-family: 微軟正黑體;
    }
    .emoji_action{
        font-size: 17px;
        margin-left: 2px;
        border-radius: 3px;
    }
    .emoji_action , .tag_list_action{
        color: #ccc;
        border: solid 2px #ccc;
        padding: 2px;
        cursor: pointer;
    }
    .tag_list_action{
        font-size: 18px;
        border-radius: 6px;
        margin-right: 5px;
    }
    .emoji_action{
        font-size: 17px;
        margin-left: 2px;
        border-radius: 3px;
    }
''')

#定義TABLE表符結果表格元素:輸入res的表符字典串列，回傳TABLE表符果
def TABLE_emojiReslut(res_emoji_dict_list):
    emoji_dict_list=json.loads(res_emoji_dict_list.text)
    #取消預設動作:雙擊選取
    def cancelSelection(ev):
        window.getSelection().removeAllRanges()
    table=TABLE(
        Class="",
        id="table_emoji_result",
    ).bind('dblclick',cancelSelection)
    table<=TR_emojiReslut()
    for emoji_dict in emoji_dict_list:
        emoji_url=emoji_dict['url']
        emoji_id=emoji_dict['id']
        tag_str_list=emoji_dict['tags']
        table<=TR_emoji(emoji_url,emoji_id,tag_str_list)
    return table
    
#定義TABLE表符結果表格樣式
thEmoji_width=60
AddStyle('''
    th,td{
        border:solid 2px #adadad;
    }
    table{
        border-collapse: collapse;
        border-spacing: 0;
        border: 3px solid #838de9;
        width:100%;
        max-width:1000px;
        box-shadow: #aaa 1px 1px 10px;
    }
    tr>th:nth-child(1){
        width:'''+str(thEmoji_width)+'''px;
    }
    th{
        color:black;
        background-color:#838de9;
        height:36px;
    }
    th>p{
        text-align:center;
        margin: 0;
    }
    td{
        word-break:break-all;
    }


    ''')



#定義組合表符DIV_TABLE元素
def DIV_CombindEmojiTable(combind_url_list,emoji_url):

    #定義動作:從組合表符頁面返回表符TABLE頁面，並將刪除組合表符的訊息傳至前頁的組合表符ICON
    def BackToEmojiTablePage(ev):
        btn_back_elt=ev.currentTarget
        #清除自組合表符頁面
        doc['div_combind_emoji_table'].remove()
        #顯示表符TABLE頁面、頁籤DIV元素、標籤搜尋結果區塊DIV元素
        doc['table_emoji_result'].classList.remove("hidden")
        doc['emoji_page_btns'].classList.remove("hidden")
        doc['search_tag_result'].classList.remove("hidden")
        doc<=A(
            id="a_led_to_emoji_tr",
            href=f"#{EmojiUrlId(btn_back_elt.emoji_url)}"
        )
        doc['a_led_to_emoji_tr'].click()
        doc['a_led_to_emoji_tr'].remove()
        
        do_delete_combind_url_list=btn_back_elt.do_delete_combind_url_list
        #刪除組合表符ICON的附加元素，組合表符串列，內的組合表符
        #獲取對應表符IMG元素以及對應組合表符ICON元素
        img_emoji_elt=doc[f'{EmojiUrlId(emoji_url)}']
        icon_combind_emoji_elt=ParentElt(img_emoji_elt,"TR").nextSibling.select('.icon_combind_emoji ')[0]
        #進行刪除組合表符ICON的附加元素
        for do_delete_combind_url in do_delete_combind_url_list:
            icon_combind_emoji_elt.combind_url_list.remove(do_delete_combind_url)
    
    #定義動作:刷新組合表符預覽圖片
    def ReloadCombindEmoji(ev):
        for img_emoji_elt in ev.currentTarget.parent.select('img'):
            img_emoji_elt.src=img_emoji_elt.src
    
    #定義動作:複製組合表符網址
    def doCopyCombindEnoji(ev):
        btn_copy_combind_emoji_elt=ev.currentTarget
        combind_url=btn_copy_combind_emoji_elt.combind_url
        CopyTextToClipborad(combind_url)
        alert("複製成功")

    #定義動作:跳至新增組合表符頁面
    def _JumpToAddCombindEmoji(ev):
        btn_add_combind_emoji_elt=ev.currentTarget
        emoji_url=btn_add_combind_emoji_elt.emoji_url
        #返回表符列表TABLE
        JumpToAddCombindEmoji(emoji_url)

    #定義動作:刪除組合表符
    def DeleteCombindEmoji(ev):
        do_delete_combind_emoji=confirm("確定要刪除這個組合表符嗎?")
        if do_delete_combind_emoji:
            btn_delete_combind_emoji_elt=ev.currentTarget
            SendRequest_DeleteCombindEmoji(btn_delete_combind_emoji_elt.combind_url,btn_delete_combind_emoji_elt)
        else:
            pass

    #設置組合表符DIV_TABLE元素
    div_elt=DIV(id="div_combind_emoji_table")

    div_elt<=IMG(src=emoji_url)+BR()

    #設置返回表符TABLE按鈕
    btn_back_elt=BUTTON("返回",id="btn_back")#,Class="w3-btn w3-ripple w3-green")
    btn_back_elt.emoji_url=emoji_url
    btn_back_elt.do_delete_combind_url_list=[] #紀錄刪除的組合組表，以便將資訊回傳至表符TABLE的組合表符icon元素
    btn_back_elt.bind("click",BackToEmojiTablePage)

    btn_add_combind_emoji_elt=BUTTON("新增組合表符",style={"margin":"10px 0px 15px 8px"})
    btn_add_combind_emoji_elt.emoji_url=emoji_url
    btn_add_combind_emoji_elt.bind("click",_JumpToAddCombindEmoji)

    div_elt<=btn_back_elt
    div_elt<=btn_add_combind_emoji_elt
    
    table_elt=TABLE(id="table_combind_emoji")
    for combind_url_with_vertical_symbol in combind_url_list:
        div_combindEmoji_elt=DIV(id="div_img_combind_emoji")
        emoji_url_list_list=[[emoji_url.replace("*","") for emoji_url in combind_url_line.split("**")] for combind_url_line in combind_url_with_vertical_symbol.split("|")]
        for emoji_url_list in emoji_url_list_list:
            for emoji_url in emoji_url_list:
                div_combindEmoji_elt<=IMG(src=emoji_url).bind("click",lambda ev:JumpToSearchEmoji(ev.currentTarget.src))
            div_combindEmoji_elt<=BR()
        
        #設置複製組合表符網址按鈕，並事先將含有直線符號斷行的組合表符網址改為正規網址
        combind_url=combind_url_with_vertical_symbol.replace("|","\n")
        btn_copy_combind_emoji_elt=BUTTON("複製組合表符網址")
        btn_copy_combind_emoji_elt.combind_url=combind_url
        btn_copy_combind_emoji_elt.bind("click",doCopyCombindEnoji)
        
        #設置刷新組合表符圖片預覽按鈕
        btn_reload_combind_emoji_elt=BUTTON("重載圖片",id="btn_reload_combind_emoji",style={"margin":"10px 0px 15px 8px"})
        btn_reload_combind_emoji_elt.bind("click",ReloadCombindEmoji)

        btn_delete_combind_emoji_elt=BUTTON("刪除",id="btn_delete_combind_emoji",style={"margin":"10px 0px 15px 8px"})
        btn_delete_combind_emoji_elt.combind_url=combind_url
        btn_delete_combind_emoji_elt.bind("click",DeleteCombindEmoji)

        div_combindEmoji_elt<=btn_copy_combind_emoji_elt
        div_combindEmoji_elt<=btn_reload_combind_emoji_elt
        div_combindEmoji_elt<=btn_delete_combind_emoji_elt

        table_elt<=TR(TD(div_combindEmoji_elt))
        
    div_elt<=table_elt
    return div_elt
AddStyle('''
    #div_img_combind_emoji img{
        cursor:pointer;
        vertical-align: top;
    }
    #div_img_combind_emoji img:hover{
        opacity: 0.5;
    }
''')