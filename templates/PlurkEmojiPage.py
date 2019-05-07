#全域函數:版本號
VERSION="1.3.0"

#更改網頁標題
doc.select("head title")[0].text+=f" {VERSION}"

#定義DIV網頁header區塊
def DIV_header():
    div_elt=DIV(id="div_header",Class="w3-row-padding w3-green")
    H1_title_elt=H1(B(f"噗浪表符庫 {VERSION}"
                    ,style={
                        "font-family":"微軟正黑體"
                    }))
    div_elt<=H1_title_elt
    return div_elt
AddStyle('''
    #div_header{
        height: 100px;
        position: relative;
        z-index: 10;
    }
''')

#定義DIV導覽列區塊
def DIV_bars():
    #定義A導覽列按鈕元素
    def DIV_ButtonBar(button_name,id=None):
        unactive_className="w3-bar-item w3-button w3-large w3-hover-blue"
        div_elt=DIV(button_name,Class=unactive_className)
        if id:            
            div_elt.id=id
        return div_elt
    #設置DIV導覽列區塊
    div_elt=DIV(Class="w3-bar w3-black bars")
    #定義導覽列按鈕被點擊時:顯示/切換對應子頁面，更換導覽列按鈕樣式
    def onClick_bar(ev):
        #獲取要跳至的DIV子頁面
        bar_name=ev.currentTarget.text
        div_jumpto_elt=doc.select(f'#{bar_name}')[0]
        #獲取當前的DIV子頁面
        div_previous_elt=[div_elt for div_elt in doc.select('div.subpage') if div_elt.style.display!="none"][0]
        #當頁面跳轉時才執行更換動作
        if div_jumpto_elt!=div_previous_elt:
            div_previous_elt.style.display="none"
            div_jumpto_elt.style.display="block"
            #更換bar樣式
            aButton_bar_previous_elt=doc.select(".AButton_bar_actived")[0]
            aButton_bar_previous_elt.classList.remove("AButton_bar_actived")
            aButton_bar_jumpto_elt=ev.currentTarget
            aButton_bar_jumpto_elt.classList.add("AButton_bar_actived")
    #排版:設置導覽列bars的順序
    '第一個bar:初始設定已經被按下'
    AButton_bar_frist=DIV_ButtonBar("搜尋表符",id="button_bar_search_emoji")
    AButton_bar_frist.classList.add("AButton_bar_actived")
    div_elt<=AButton_bar_frist.bind("click",onClick_bar)
    '其他bars'
    div_elt<=DIV_ButtonBar("新增表符",id="button_bar_add_emoji").bind("click",onClick_bar)
    div_elt<=DIV_ButtonBar("更新日誌",id="button_bar_update_diary").bind("click",onClick_bar)
    div_elt<=DIV_ButtonBar("其他作品",id="button_bar_other_production").bind("click",onClick_bar)
    div_elt<=DIV_ButtonBar("關於作者",id="button_bar_about_author").bind("click",onClick_bar)
    #設定bar被按下時的樣式
    AddStyle("""
        .AButton_bar_actived{
            background-color:gray;
        }
        .bars{
            margin: 0px 0px 1em;
            font-family: 微軟正黑體;
            position: relative;
            z-index: 10;
        }
        #其他作品, #關於作者{
            margin: 50px 35px;
        }
    """)

    return div_elt

def DIV_siteInfo():
    #送出請求，顯示站內資訊(表符數和標籤數)
    def SendRequest_showSiteInfo():
        req = ajax.ajax()
        req.bind('complete',OnComplete_showSiteInfo)
        url='/PlurkEmojiHouse/NumOfEmoji_and_NumOfTag'
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()

    #處理回應，顯示站內資訊(表符數和標籤數)
    def OnComplete_showSiteInfo(res):
        numOfEmoji,numOfTag=json.loads(res.text)
        doc['div_site_info']<=SPAN(
            f'表符數量:{numOfEmoji}　標籤數量:{numOfTag}　　',
            Class="span_site_info",
        )

    div_elt=DIV(id='div_site_info')
    div_fb_info_elt=doc.select('.fb-like')[0]
    div_elt<=div_fb_info_elt
    #載入網頁後，在頁面右側顯示表符數和標籤數
    SendRequest_showSiteInfo()

    return div_elt
AddStyle('''
    #div_site_info{
        width: 90%;
        max-width: 1000px;
        margin-left: 20px;
        position: relative;
        z-index: 9;
    }
    .span_site_info{
        font-size: 9px;
        float: right;
        margin-top: 3px;
    }
    .fb-like{
        float: right;
        margin-bottom: 7px;
        margin-right: 0 !important;
    }
''')


#--定義子頁面，DIV的id必須要和導覽列文字一樣--

#定義DIV子頁面:搜尋表符
def DIV_subpage_searchEmoji():
    div_elt=DIV(id="搜尋表符",Class="subpage",style={"display":"block"})
    div_card_elt=DIV(Class="div_input_card")
    div_card_elt<=BR()
    #定義[搜尋表符標籤文字框]按下Enter送出
    def pressEnterToSend(ev):
        #在ev有附加屬性key時才執行(避免出現錯誤)
        if hasattr(ev, 'key'):
            if ev.key=="Enter":
                doc['search_tag_btn'].click()
    #設置搜尋表符標籤文字框
    input_text_elt=INPUT(type="text"
                        ,id="search_tag"
                        ,placeholder="輸入角色/作品名/動詞/形容詞..."
                        ,Class="placeholder_style"
                        ).bind('keydown',pressEnterToSend)
    #設置搜尋表符標籤文字框:套用文字提示
    input_text_elt=DIV_showTipText(input_text_elt
                                    ,'用逗號","區隔多個標籤'
                                    ,show_ev_list=["focusin"]
                                    ,hide_ev_list=["keydown"
                                                  ,"focusout"]
                                    ,width="180px")
    div_card_elt<=input_text_elt
    #設定搜尋框CSS樣式
    AddStyle("""
        #div_search_tag {
            float:left;
        }
        .placeholder_style::placeholder{
            font-size:12px;
            color:#555;
        }
        #search_tag:focus{
            border: 2px solid lightblue !important;
            box-shadow:0px 0px 3px rgb(75, 119, 241);
            margin-right:7px !important;
        }
        #search_tag{
            border: 1px solid rgb(204, 204, 204);
            border-radius: 15px;
            outline: none;
            height: 35px;
            padding: 10px;
            margin-right: 7px;
            width: 250px;
        }
        @media only screen and (max-width: 600px) {
            #search_tag {
                width: 150px;
            }
        }
        @media only screen and (max-width: 400px) {
            #search_tag {
                width: 100px;
            }
        }
    """)

    #設置搜尋表符按鈕
    div_card_elt<=BUTTON("搜尋"
                        ,id="search_tag_btn"
                        ,style={"margin-bottom":"7px"}
                        ).bind("click",SendRequest_searchEmoji)
    #設置顯示全部按鈕
    div_card_elt<=BUTTON("顯示全部"
                        ,id="show_all_emoji_btn"
                        ,style={"margin-left":"7px"}
                        ).bind("click",SendRequest_searchEmoji)
    div_elt<=div_card_elt

    #設置表符搜尋結果DIV_TABLE
    div_emoji_result_table=DIV(
        Class="div_emoji_result_table_area",
        id="emoji_result_table"
    )
    
    #設置搜尋標籤結果DIV
    div_search_tags_result_elt=DIV(
        id="search_tag_result",
        style={
            "margin":"15px 20px",
            "line-height":"28px",
        }
    )
    #設置說明區塊
    def DIV_description():
        #定義綁定同步滑鼠覆蓋動作以顯示文字框
        def ShowDescription(ev):
            mouseover_ev = window.MouseEvent.new("click")
            icon_description_elt=doc['div_description'].select('.fa-question-circle')[0]
            icon_description_elt.dispatchEvent(mouseover_ev)
        div_elt=DIV(style={"float":"right"},id="div_description")
        div_elt<=DIV_showTipText(
            I(Class="far fa-question-circle")+"說明",
            '使用步驟說明:'+BR()
            +'1. 搜尋表符關鍵字(或者直接點擊標籤)'+BR()
            +'2. 複製表符圖片網址(或者直接點擊表符)'+BR()
            +'3. 貼上至噗浪即可顯示表符'+BR()
            +'(※網址的前後要留空白才能成功顯示)'
            )

        return div_elt

    div_card_elt<=DIV_description()

    #--排版--#
    #置入搜尋標籤結果DIV
    div_elt<=div_search_tags_result_elt
    #置入表符結果TABLE
    div_elt<=div_emoji_result_table+BR()
    #置入表符結果頁籤按鈕區塊
    div_elt<=DIV(id="emoji_page_btns",style={"margin-left":"20px"})



    return div_elt
AddStyle('''
    .div_emoji_result_table_area{
        width: 90%;
        margin: 20px 0px 0px 20px;
    }

    #div_description .tooltiptext{
        width: 290px !important;
        text-align: left !important;
        padding: 5px !important;
        margin-left: -250px !important;
    }

    #div_description .span_tooltip_trangle{
        margin-left: 100px !important;
    }
    #div_description{
        margin-top: 5px;
        color: #aaa;
        cursor:pointer;
    }
    #div_description:hover{
        color: #68dcc8;
    }
''')

#定義DIV子頁面:新增表符
def DIV_subpage_addEmoji():
    #設置輸出用DIV
    div_elt=DIV(id="新增表符",Class="subpage",style={"display":"none"})
    #設置背景卡片DIV區塊
    div_card_elt=DIV(
        Class="div_input_card",
        id="div_adding_emoji_input_area_elt"
    )
    div_card_elt<=BR()
    
    def ChangeAddingEmojiMethod(ev):
        #獲取更換前的新增表符DIV元素，並將其隱藏
        div_jump_off_elt=[div for div in doc['div_adding_emoji_input_area_elt'].select(".adding_emoji_input_area") if ("hidden" not in div.classList)][0]
        div_jump_off_elt.classList.toggle("hidden")
        #獲取指定更換的新增表符DIV元素，並將其顯現
        if ev.currentTarget.value=="表符圖片網址":
            doc['div_input_emoji_url_to_add_emoji_elt'].classList.toggle("hidden")
        elif ev.currentTarget.value=="公開噗文網址":
            doc['div_input_plurk_url_to_add_emoji_elt'].classList.toggle("hidden")
        elif ev.currentTarget.value=="噗文網頁原始碼":
            doc['div_input_html_to_add_emoji_elt'].classList.toggle("hidden")


    select_elt=SELECT(style={"margin-bottom":"15px"})
    select_elt<=OPTION("表符圖片網址")
    select_elt<=OPTION("公開噗文網址")
    select_elt<=OPTION("噗文網頁原始碼")
    select_elt.bind("change",ChangeAddingEmojiMethod)
 
    #定義綁定按下Enter送出新增表符
    def pressEnterToSend(ev):
        #在ev有附加屬性key時才執行(避免出現錯誤)
        if hasattr(ev, 'key'):
            if ev.key=="Enter":
                doc['button_send_to_add_emoji'].click()

    #設置輸入表符圖片url新增表符DIV元素
    def DIV_input_emoji_url_to_add_emoji():
        div_elt=DIV(
            Class="adding_emoji_input_area ",
            id="div_input_emoji_url_to_add_emoji_elt",
            style={"float":"left"},
        )
        input_elt=INPUT(
            type="text",
            id="input_input_emoji_url_to_add_emoji_elt",
            placeholder="輸入表符圖片網址",
            Class="placeholder_style input_url_elt",
        ).bind('keydown',pressEnterToSend)
        
        div_elt<=input_elt
        div_elt<=BUTTON(
            "送出",
            id="button_send_to_add_emoji",
            ).bind("click",SendRequest_addEmoji)+BR()
        div_elt<=SPAN("例如 https://emos.plurk.com/2658f2e2cffb4e9d6b72d4a6374597f9_w48_h48.jpeg",Class="span_example_msg_elt")

        return div_elt


    #設置輸入噗文網址新增表符DIV元素
    def DIV_input_plurk_url_to_add_emoji():
        div_elt=DIV(
            Class="adding_emoji_input_area hidden",
            id="div_input_plurk_url_to_add_emoji_elt",
            style={"float":"left"},
        )
        input_elt=INPUT(
            type="text",
            id="input_input_plurk_url_to_add_emoji_elt",
            placeholder="輸入噗文網址",
            Class="placeholder_style input_url_elt",
        ).bind('keydown',pressEnterToSend)
        
        div_elt<=input_elt
        div_elt<=BUTTON(
            "送出",
            id="button_send_to_add_emoji",
            ).bind("click",SendRequest_addEmoji)+BR()
        div_elt<=SPAN("例如 https://www.plurk.com/p/n0z4wz",Class="span_example_msg_elt")
        return div_elt
    
    #設置輸入噗文網頁原始碼新增表符DIV元素
    def DIV_input_html_to_add_emoji():
        #設置說明DIV區塊
        def DIV_description():
            div_elt=DIV()
            div_elt<=SPAN("可將這個")
            div_elt<=A(
                "複製網頁原始碼",
                href='''javascript: function CopyBodyHtml() { const el = document.createElement('textarea'); el.value = document.body.innerHTML; document.body.appendChild(el); el.select(); document.execCommand('copy'); document.body.removeChild(el); if (document.body.innerHTML.includes('class="emoticon_my')) { alert("複製成功!"); } }; CopyBodyHtml(); void(0);''',
            )
            div_elt<=SPAN("連結拖曳至書籤列使用")

            return div_elt
        div_elt=DIV(
            Class="adding_emoji_input_area hidden",
            id="div_input_html_to_add_emoji_elt",
            style={"float":"left"},
        )
        textarea_plurk_html_elt=TEXTAREA(
            id="textarea_input_html_to_add_emoji_elt",
            Class="input_url_elt",
            )

        div_elt<=textarea_plurk_html_elt
        div_elt<=BUTTON(
            "送出",
            id="button_send_to_add_emoji",
            style={"position":"absolute","margin-top":"40px"},
            ).bind("click",SendRequest_addEmoji)
        div_elt<=DIV_description()
        
        return div_elt

    #排版
    div_card_elt<=SPAN("選擇輸入 ")+select_elt+BR()
    div_card_elt<=DIV_input_emoji_url_to_add_emoji()
    div_card_elt<=DIV_input_plurk_url_to_add_emoji()
    div_card_elt<=DIV_input_html_to_add_emoji()

    div_elt<=div_card_elt
    div_elt<=DIV("新增表符中...",Class="hidden msg_string",id="adding_emoji_msg")
    div_elt<=DIV("輸入的表符網址錯誤",Class="hidden msg_string",id="incorrect_emoji_url_msg")
    div_elt<=DIV(
        id="div_show_adding_emoji_result_table_area",
        Class="div_emoji_result_table_area",
    )
    
    
    return div_elt
AddStyle('''
    a {
        color:#0064ff;
    }
    a:hover{
        color:#00ceff;
    }
    .msg_string{
        width: 90%;
        margin: 20px 0px 0px 20px;
    }
    .div_input_card{
        border: 1px solid rgb(204, 204, 204);
        border-radius: 10px;
        margin: 5px 20px;
        box-shadow: grey 1px 1px 3px;
        padding: 2px 20px 10px;
        display: table;
        width: 90%;
        max-width: 1000px;
    }
    textarea {
        padding: 2px;
        width: 200px;
        height: 70px;
        border-radius: 10px;
        font-size: 8px;
        margin-right: 7px;
        outline: none;
    }
    .span_example_msg_elt{
        color: #bbb;
        font-size: 8px;
        word-break: break-all;
    }
    input.input_url_elt{
        border: 1px solid rgb(204, 204, 204);
        border-radius: 15px;
        outline: none;
        height: 35px;
        padding: 10px;
        margin-right: 7px;
        margin-bottom: 7px;
        
    }
    .input_url_elt:focus{
        border: 2px solid rgb(255,209,112) !important;
        box-shadow:0px 0px 3px rgb(243,236,79);
        margin-right:5px !important;
    }
''')

#定義子頁面:更新日誌
def DIV_subpage_updateDiary():
    div_elt=DIV(id="更新日誌",Class="subpage",style={"display":"none"})
    div_elt<=DIV(IFRAME(src="https://docs.google.com/document/d/e/2PACX-1vT0Z3y-e_t7ZIWRjcfOr-0f22uHqQLTDwrtNCeaPJNoI78KyviNLREvLV-eVId9MezNuRlqk2hCsHdI/pub?embedded=true"),id="warp_iframe")
    return div_elt

AddStyle('''
    #更新日誌 #warp_iframe{
        overflow: hidden;
        width: 100%;
    }
    #更新日誌 iframe{
        width: 900px;
        height: 3000px;
        margin-top: -80px;
        margin-left: -63px;
        padding-right: 380px;
        border: 0;
    }
''')


def DIV_otherProduction():
    div_elt=DIV(id="其他作品",Class="subpage",style={"display":"none"})
    div_elt<=H4("【網站工具】")
    div_elt<=A(
        IMG(
            src="https://i.imgur.com/QhJwVs1.png",
            width="200px",
        ),
        href="https://sites.google.com/view/ahktool/",
        target="_blank",
    )
    div_elt<=P("● 一個提高工作效率的網站工具 - 快捷鍵語法產生器")
    div_elt<=DIV(
        IFRAME(
            src="https://www.youtube.com/embed/videoseries?list=PLtO1yDnSMpUPDN9rkqTgEIOGfumA86AyG",
            frameborder="0",
            allow="autoplay; encrypted-media",
            allowfullscreen=True,
            Class="youtube_playlist",
        ),
        Class="youtube_playlist_container"
    )
    return div_elt

AddStyle('''
    .youtube_playlist_container {
        position: relative;
        width: 500px;
        height: 300px;
        padding-bottom: 56.25%;
    }
    .youtube_playlist {
        position: absolute;
        top: 0;
        left: 0;
        width: 500px;
        height: 300px;
    }
    @media screen and (max-width: 500px) {
        .youtube_playlist_container {
            position: relative;
            width: 300px;
            height: 180px;
            padding-bottom: 56.25%;
        }
        .youtube_playlist {
            position: absolute;
            top: 0;
            left: 0;
            width: 300px;
            height: 180px;
        }
    }
''')

def DIV_about_author():
    div_elt=DIV(id="關於作者",Class="subpage",style={"display":"none"})
    div_elt<=P("● 作者信箱")
    div_elt<=P("papple23g@gmail.com")+HR()
    div_elt<=P("● 作者噗浪")
    div_elt<=IFRAME(
        src="https://www.plurk.com/getWidget?uid=4180727&amp;h=375&amp;w=200&amp;u_info=2&amp;bg=FF574D&tl=EEEBF0",
        width="300",
        frameborder="0",
        height="375",
        scrolling="no",
    )
    return div_elt



#排版:置入DIV網頁header區塊
doc<=DIV_header()
doc<=DIV_bars()
doc<=DIV_siteInfo()
doc<=DIV_subpage_searchEmoji()
doc<=DIV_subpage_addEmoji()
doc<=DIV_subpage_updateDiary()
doc<=DIV_otherProduction()
doc<=DIV_about_author()

##進入前直接顯示全部表符
doc['show_all_emoji_btn'].click()