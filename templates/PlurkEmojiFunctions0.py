from browser import document as doc
from browser import window,ajax,alert,bind,timer
from browser.html import *
import json

#全域函數
# - 當前子頁籤目錄
SUB_PAGE_INDEX=0
# - 第一次送出搜尋請求(顯示第一頁)
FRIST_REQ=None
# - 第一次送出搜尋請求的關鍵字
SEARCH_TAG_OF_FRIST_REQ=None
# - 
DIV_SUBPAGE_BEFORE_JUMP=None

#送出請求，顯示站內資訊(表符數和標籤數)
def send_request_show_site_info():
    req = ajax.ajax()
    req.bind('complete',on_complete_show_site_info)
    url='/PlurkEmojiHouse/NumOfEmoji_and_NumOfTag'
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

#處理回應，顯示站內資訊(表符數和標籤數)
def on_complete_show_site_info(res):
    numOfEmoji,numOfTag=json.loads(res.text)
    doc['site_info']<=SPAN(
                        f'表符數量:{numOfEmoji}　標籤數量:{numOfTag}　　',
                        style={'font-size':'9px'}
                      )

#載入網頁後，在頁面右側顯示表符數和標籤數
send_request_show_site_info()

#定義標籤樣式，附帶超連結
def Span_tag(tag_str,emoji_id_str):
    return A(SPAN(tag_str,id=emoji_id_str+"__tag__"+tag_str,Class="tag_btn"),href="#",style={'text-decoration':'none'})+SPAN(" ")

#處理回應資料，變成表符字典
def EmojiDictListOnePage_and_NumOfBtn_fromRespond(res):
    search_result_data_list=json.loads(res)
    emoji_dict_list_one_page,num_of_btn=search_result_data_list
    return emoji_dict_list_one_page,num_of_btn

#單頁表符結果清單Table(無綁定事件)以及所有單頁顯示的表符id串列
def table_without_binding_and_showed_id_list_and_showed_tag_id_list(emoji_dict_list):
    table=TABLE(Class="w3-card w3-table w3-border")
    table<=TR(TH("表符")+TH("標籤"+SPAN(" (點擊:搜尋，右鍵:刪除)"))+TH("新增標籤"))
    showed_id_list=[]
    showed_tag_id_list=[]
    for emoji_dict in emoji_dict_list:
        id=emoji_dict["id"]
        url=emoji_dict["url"]
        tag_list=emoji_dict["tags"].split(",")
        td_tag_list=TD()
        for tag_str in tag_list:
            if tag_str:
                td_tag_list<=Span_tag(tag_str,str(id))
                #標籤的id格式: [str_id]__tag__[str_tagName]
                showed_tag_id_list.append(str(id)+"__tag__"+tag_str)
        td_tag_list<=SPAN(id="td_tag_list"+str(id),style={"text-align":"left"})
        td_tag_list<=SPAN("新增標籤中...",Class="span_adding_tag_msg",id="span_adding_tag_msg"+str(id),style={'display':'none'})

        table_row=TR(
            TD(DIV(A(IMG(src=url,Class="emoji_pic",id="emoji_img"+str(id)),href="#!")+SPAN("複製表符網址",Class="tooltiptext",id="tooltiptext"+str(id)),Class="tooltip"))
            +td_tag_list
            +TD(
                INPUT(type="text",id="add_tag_text"+str(id),size="5")
                +SPAN(" ")
                +BUTTON("新增",id="add_tag_btn"+str(id))
                ,title="輸入 : 人物名稱/作品名稱/動詞/形容詞\n可用逗號分隔多個想要新增的標籤"
            )
        )
        showed_id_list.append(id)
        table<=table_row
    return table,showed_id_list,showed_tag_id_list

#定義動作，幫一個表符Table進行綁定
def binding_table(showed_id_list,showed_tag_id_list,click_tag_search=True,rightClick_tag_del=True):
    #定義動作，按下Enter按鍵新增標籤文字欄訊息
    def add_tag_pressEnter(ev):
        id=ev.currentTarget.id[len("add_tag_text"):]
        if ev.keyCode==13:
            click_event = window.MouseEvent.new("click")
            doc["add_tag_btn"+str(id)].dispatchEvent(click_event)
    
    #定義動作，點擊表符可以複製Url，並顯示"已複製"提示文字，過幾秒後回復提示文字
    def CopyEmojiUrl(ev):
        #取得點選的表符ID
        id=ev.currentTarget.id[len("emoji_img"):]
        #複製表符Url到剪貼簿
        emoji_url=ev.currentTarget.src
        doc['copy_text'].style.display="inline"
        doc['copy_text'].value=emoji_url
        doc['copy_text'].select()
        doc.execCommand('copy')  #執行複製的動作
        doc['copy_text'].style.display="none"
        #改變提示文字
        def change_tooltiptext_back():
            doc["tooltiptext"+str(id)].text="複製表符網址"
        doc["tooltiptext"+str(id)].text="已複製"
        timer.set_timeout(change_tooltiptext_back, 1500)

    #設定綁定事件集合
    # - 設定標籤相關的綁定
    for id in showed_id_list:
        doc["add_tag_btn"+str(id)].bind("click",send_request_add_tag)
        doc["add_tag_text"+str(id)].bind("keyup",add_tag_pressEnter)
        doc["emoji_img"+str(id)].bind("click",CopyEmojiUrl)
    # - 設定點擊標籤送出查詢的綁定
    for showed_tag_id in showed_tag_id_list:
        if click_tag_search:
            doc[showed_tag_id].bind("click",send_request_search_emoji)
        if rightClick_tag_del:
            doc[showed_tag_id].bind("contextmenu",send_request_delelte_tag)

#定義切頁動作:更改頁籤按鈕樣式，切換子頁面
def swicth_page_btn(ev):
    global SUB_PAGE_INDEX
    i_page_current=SUB_PAGE_INDEX
    i_page_jump_to=int(ev.currentTarget.id[len("btn_page"):])-1
    #如果目前的頁面等於指定跳轉頁面，則不動作
    if i_page_current==i_page_jump_to:
        pass
    #如果目前的頁面不等於指定跳轉頁面
    else:
        #將目前子頁面留白
        doc['result'].style.visibility="hidden"
        #替換頁籤按鈕顏色
        current_btn=doc["btn_page"+str(i_page_current+1)]
        jump_to_btn=doc["btn_page"+str(i_page_jump_to+1)]
        current_btn.className=""
        jump_to_btn.className="btn_pressed"
        #改變全域函數
        SUB_PAGE_INDEX=i_page_jump_to
        #將點擊頁籤按鈕事件傳遞至請求函數
        send_request_search_emoji(ev)

#定義換頁的請求操作
def show_result_on_page(emoji_dict_list_one_page):
    global SUB_PAGE_INDEX
    #將被留白的結果區塊替換成新的結果後再顯示
    div_show_result_page=doc["result"]
    table,showed_id_list,showed_tag_id_list=table_without_binding_and_showed_id_list_and_showed_tag_id_list(emoji_dict_list_one_page)
    div_show_result_page.clear()
    div_show_result_page<=table
    doc['result'].style.visibility="visible"
    binding_table(showed_id_list,showed_tag_id_list)

num_of_emoji_per_page=20
#根據頁面數量，準備子頁面容器和頁籤按鈕，並綁定頁籤按鈕
def prepare_container(emoji_dict_list_frist_page,num_of_btn):
    num_of_page=num_of_btn
    #清空之前的頁籤按鈕區塊
    doc['btn_of_pages'].clear()
    #清空之前的結果清單
    doc['result'].clear()
    #置入頁籤按鈕元素
    for i_page in range(num_of_page):
        btn_page=BUTTON(str(i_page+1),id="btn_page"+str(i_page+1))
        doc['btn_of_pages']<=A(btn_page,href="#!")
    #壓下第一個按鈕
    doc['btn_page1'].className="btn_pressed"

    #綁定所有頁籤按鈕，每個頁籤按鈕都是送出搜尋請求
    for i_page in range(num_of_page):
        doc["btn_page"+str(i_page+1)].bind('click',swicth_page_btn)

    #顯示第一頁資料
    table,showed_id_list,showed_tag_id_list=table_without_binding_and_showed_id_list_and_showed_tag_id_list(emoji_dict_list_frist_page)
    doc['result']<=table
    binding_table(showed_id_list,showed_tag_id_list)
   
#搜尋表符中途時的提醒等待文字
def loading_search_emoji(res):
    doc["searching_msg"].style.display="inline"

#送出請求，刪除標籤
def send_request_delelte_tag(ev):
    ev.preventDefault() #防止出現右鍵選單
    span_tag_id=ev.currentTarget.id
    emoji_id_str,tag_name=span_tag_id.split("__tag__")
    comfirm_box=("確定要刪除 [{}] 這個標籤嗎?".format(tag_name))
    going_to_del_tag=window.confirm(comfirm_box)
    if going_to_del_tag:
        req = ajax.ajax()
        url='/PlurkEmojiHouse/delete_tag?emoji_id='+emoji_id_str+'&tag_name='+tag_name
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()
        ev.currentTarget.style={"display":"none"}

#完成查詢回應時，呈現結果清單
def on_complete_search_emoji(res):
    doc["searching_msg"].style.display="none"
    global FRIST_REQ
    if res.status==200 or res.status==0:
        if res.text[0]==u'沒':
            #doc["result"].clear()
            doc["btn_of_pages"].clear()
            doc["result"].clear()
            doc["result"]<=res.text
        #成功收到表符字典資料時
        else:
            emoji_dict_list_one_page,num_of_btn=EmojiDictListOnePage_and_NumOfBtn_fromRespond(res)
            doc["result"].clear()
            #若是第一次的搜尋請求
            if FRIST_REQ:
                prepare_container(emoji_dict_list_one_page,num_of_btn)
            #若是換頁的搜尋請求
            else:
                show_result_on_page(emoji_dict_list_one_page)

    else:
        doc["result"].html = "error "+res.text

    #如果是以網址新增表符，則新增完成後清空輸入的網址
    doc["input_add_emoji"].value=""


#等待搜尋標籤時的動作
def loading_search_tags(ev):
    doc['search_tag_result']<=SPAN("　搜尋標籤中...")

#完成搜尋標籤時的動作
def on_complete_search_tags(res):
    tag_list,num_of_tagged_list=json.loads(res.text)

    #根據被標籤次數排序內容:先倆倆綁定，排序，再解除綁定
    ziped_tag_data_list=zip(tag_list,num_of_tagged_list)
    ziped_tag_data_list=sorted(ziped_tag_data_list,key=lambda x:x[1],reverse=True)
    tag_list,num_of_tagged_list=zip(*ziped_tag_data_list)

    doc['search_tag_result'].clear()
    for i_tag in range(len(tag_list)):
        tag_str=tag_list[i_tag]
        num_of_tagged=num_of_tagged_list[i_tag]
        #顯示包含關鍵字的標籤和備標註的次數
        doc['search_tag_result']<=A(SPAN_tag(
                                            tag_str
                                            +SPAN(" "+str(num_of_tagged),
                                                style={'color':'#ddd'}),
                                        id="tag_searched__"+tag_str,
                                        Class="tag_btn"),
                                        href="#",
                                        style={'text-decoration':'none'}
                                    )+SPAN(" ")
        doc["tag_searched__"+tag_str].bind('click',send_request_search_emoji)

#請求函數，送出標籤或網址，搜尋表符以及相似標籤
def send_request_search_emoji(ev):
    global SUB_PAGE_INDEX
    global FRIST_REQ
    global SEARCH_TAG_OF_FRIST_REQ

    #任何搜尋都是為第一次請求，除了頁籤搜尋
    FRIST_REQ=True
    
    #獲取使用者輸入的搜尋關鍵字
    # - 處理點擊按鍵的搜尋方式
    ev_currentTarget=ev.currentTarget
    if ev_currentTarget.id in ["search_btn","add_emoji_btn"]:
        if ev_currentTarget.id=="search_btn":
            search_str = doc['search_tag'].value
            SEARCH_TAG_OF_FRIST_REQ=search_str
        elif ev_currentTarget.id=="add_emoji_btn":
            search_str = doc['input_add_emoji'].value
        #判斷輸入的內容是tag還是url
        if "emos.plurk.com" in search_str:
            input_type="url"
        else:
            input_type="tag"
    # - 處理頁籤按鈕的搜尋方式
    elif "btn_page" in ev_currentTarget.id:
        FRIST_REQ=False #頁籤搜尋不是第一次請求
        search_str=SEARCH_TAG_OF_FRIST_REQ #繼承上次的搜尋關鍵字
        input_type="tag"

    # - 處理點擊標籤的搜尋方式
    #   - 點擊的是表符附帶的標籤
    elif "__tag__" in ev_currentTarget.id:
        search_str = ev.currentTarget.text
        SEARCH_TAG_OF_FRIST_REQ=search_str
        doc['search_tag'].value=search_str
        input_type="tag"
    #   - 點擊的是搜尋標籤結果區塊中的標籤
    elif "tag_searched__" in ev_currentTarget.id:
        search_str = ev_currentTarget.id[len("tag_searched__"):]
        SEARCH_TAG_OF_FRIST_REQ=search_str
        doc['search_tag'].value=search_str
        input_type="tag"
    
    #根據查詢類型和情況(是否為第一次請求)，設置請求連結函數
    if input_type=="url":
        #修正開頭不是https的url
        if search_str[:8]!="https://":
            emo_i=search_str.index("emos.plurk.com")
            search_str="https://"+search_str[emo_i:]
        url='/PlurkEmojiHouse/search_by_url?search_url=%s' %(search_str)
    elif input_type=="tag":
        if FRIST_REQ:
            SUB_PAGE_INDEX = 0
        url='/PlurkEmojiHouse/search_by_tag?search_tag=%s&page=%s&fristReq=%s' %(search_str,SUB_PAGE_INDEX,FRIST_REQ)

    #使用ajax送出請求
    req = ajax.ajax()
    req.bind('complete',on_complete_search_emoji)
    req.bind('loading',loading_search_emoji)
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

    #同時搜尋相似標籤
    #若標籤區塊內的標籤被點擊時則不搜尋
    if ("tag_searched__" in ev_currentTarget.id):
        pass
    #其他搜尋關鍵字的情況則同時搜尋相似標籤
    elif (input_type=="tag") and search_str and FRIST_REQ:
        doc['search_tag_result'].clear()
        req = ajax.ajax()
        req.bind('complete',on_complete_search_tags)
        req.bind('loading',loading_search_tags)
        url='/PlurkEmojiHouse/search_tags?search_tag=%s' %(search_str)
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()



#送出增加標籤的請求
SPAN_adding_tag_msg_id=None
def send_request_add_tag(ev):
    emoji_id=int(ev.currentTarget.id[11:])
    add_tag_str=doc["add_tag_text"+str(emoji_id)].value
    if add_tag_str:
        global SPAN_adding_tag_msg_id
        SPAN_adding_tag_msg_id="span_adding_tag_msg"+str(emoji_id)
        doc[SPAN_adding_tag_msg_id].style.display="inline"
        req = ajax.ajax()
        req.bind('complete',on_complete_add_tag)
        url=f'/PlurkEmojiHouse/emoji_add_tag?id={emoji_id}&add_tag_str={add_tag_str}'
        req.open('GET',url,True)
        req.set_header('content-type','application/x-www-form-urlencoded')
        req.send()
    else:
        pass

#增加標籤完成後
def on_complete_add_tag(res):
    global SPAN_adding_tag_msg_id
    doc[SPAN_adding_tag_msg_id].style.display="none"
    emoji_id=res.text
    add_tag_str=doc["add_tag_text"+str(emoji_id)].value
    add_tag_list=[tag.strip() for tag in add_tag_str.split(",")] #去除前後空白
    td_tag_list=doc["td_tag_list"+emoji_id]
    td_tag_already_exist_list=[span.text for span in td_tag_list.parent.select('span.tag_btn') if span.text!=" "] #抓出現有的標籤名稱
    for add_tag in add_tag_list:
        if (add_tag not in td_tag_already_exist_list):
            #前端置入標籤
            if  add_tag!="":
                td_tag_list<=Span_tag(add_tag,emoji_id)
                #綁定新增的標籤事件:搜尋和刪除
                doc[emoji_id+"__tag__"+add_tag].bind("click",send_request_search_emoji)
                doc[emoji_id+"__tag__"+add_tag].bind("contextmenu",send_request_delelte_tag)
    doc["add_tag_text"+str(emoji_id)].value="" #清空新增標籤input

#綁定可使用Enter搜尋表符和標籤
@bind(doc["search_tag"],"keyup")
@bind(doc["input_add_emoji"],"keyup")
def search_tag_pressEnter(ev):
    if ev.keyCode==13:
        click_event = window.MouseEvent.new("click")
        doc["search_btn"].dispatchEvent(click_event)

#綁定清除搜尋
@bind(doc["clean_search_btn"],"click")
def clean_search(ev):
    doc['search_tag'].value=""
    click_event = window.MouseEvent.new("click")
    doc["search_btn"].dispatchEvent(click_event)
    doc["search_tag_result"].clear()

#綁定事件
doc["search_btn"].bind("click",send_request_search_emoji)
doc["add_emoji_btn"].bind("click",send_request_search_emoji)

#載入頁面時自動點擊按鈕(棄用)
#click_event = window.MouseEvent.new("click")
#doc["search_btn"].dispatchEvent(click_event)


#獲取導覽列網頁元素
a_bar_elt_list=doc.select('.w3-bar-item')

#導覽列連結的數量
num_of_bar_btn=len(a_bar_elt_list)

#導覽列按鈕樣式列表，以className進行樣式設定
a_bar_className="w3-bar-item w3-button w3-large w3-hover-blue"
a_bar_hovered_className="w3-bar-item w3-button w3-large w3-hover-blue"
a_bar_onPage_className="w3-bar-item w3-button w3-large w3-hover-blue w3-dark-grey"

#全局函數，當前被按著的導覽列按紐，初始設定是第一個按紐
A_BAR_ONPAGE=a_bar_elt_list[0]

#定義動作，改變導覽列按鈕樣式並更換子頁面
def ChangePage(ev):
    global A_BAR_ONPAGE
    a_bar_clicked=ev.currentTarget
    #點擊同一個頁面的按紐時不動作
    if a_bar_clicked==A_BAR_ONPAGE:
        pass
    #跳轉子頁面時
    else:
        #更換按鈕樣式
        A_BAR_ONPAGE.className=a_bar_className
        a_bar_clicked.className=a_bar_onPage_className
        #隱藏和顯示對應DIV子頁面
        div_onBar_left=doc[A_BAR_ONPAGE.id.replace("a_bar","div")]
        div_onBar_jumped_to=doc[a_bar_clicked.id.replace("a_bar","div")]
        div_onBar_left.style.display="none"
        div_onBar_jumped_to.style.display="inline"
        if div_onBar_jumped_to.id in ["div_search_emoji","div_add_emoji"]:
            doc['emoji_tabel'].style.display="inline"
        else:
            doc['emoji_tabel'].style.display="none"
        #更改全局函數
        A_BAR_ONPAGE=a_bar_clicked

#綁定導覽列按鈕
for a_bar in a_bar_elt_list:
    a_bar.bind('click',ChangePage)

#根據所選的批量新增方法改變輸入文字框類型
@bind(doc['select_input_plurk_type'],'change')
def change_plurk_input_type(ev):
    if ev.currentTarget.value=="option_input_plurk_url":
        doc['input_plurk_url'].style.display="inline"
        doc['input_plurk_html'].style.display="none"
    else:
        doc['input_plurk_url'].style.display="none"
        doc['input_plurk_html'].style.display="inline"

#定義功能函數，搜尋符和三明治文字夾層，回傳內容列表
def SandwichWord_list(sandWord,wichWord,text):
    len_sandWord=len(sandWord)
    len_wichWord=len(wichWord)
    com_list=[]
    i=0
    while i<len(text):
        if sandWord in text[i:]:
            i_sandWord=text.index(sandWord,i)
            i_wichWord=text.index(wichWord,i_sandWord)
            com_str=text[i_sandWord+len_sandWord:i_wichWord]
            com_list.append(com_str)
            i=i_wichWord+len_wichWord
        else:
            break
    return com_list

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
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
#定義動作，選取或取消選取表符
def selecting_or_unselect_emoji(ev):
    ev_currentTarget_className=ev.currentTarget.className
    if ev_currentTarget_className=="selected_emoji":
        ev.currentTarget.className="unselect_emoji"
    elif ev_currentTarget_className=="unselect_emoji":
        ev.currentTarget.className="selected_emoji"

#定義按鍵動作，全部選取或全部取消選取表符
def select_all_or_not(ev):
    #按下全選的動作
    if ev.currentTarget.id=="btn_select_all":
        for elt in doc.select('div.unselect_emoji'):
            elt.className="selected_emoji"
    #按下全不選的動作
    elif ev.currentTarget.id=="btn_unselect_all":
        for elt in doc.select('div.selected_emoji'):
            elt.className="unselect_emoji"

#定義請求動作，送出並新增已選取的批量表符
def send_confirm_selected_emoji_to_add(ev):
    emoji_url_selected_confirm_list=[]
    for img_elt in doc.select('div.selected_emoji>a>img'):
        emoji_url_selected_confirm_list.append(img_elt.src)
    #將以選取的表符列表，用逗號區隔，寫成一個字串
    emoji_url_selected_confirm_list_str=','.join(emoji_url_selected_confirm_list)
    
    req = ajax.ajax()
    req.bind('loading',on_loading_send_confirm_selected_emoji_to_add)
    req.bind('complete',on_complete_send_confirm_selected_emoji_to_add)
    url=f'/PlurkEmojiHouse/search_by_uuu?search_url_list={emoji_url_selected_confirm_list_str}'
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

#定義等待請求，等待增加表符時出現提醒字樣
def on_loading_send_confirm_selected_emoji_to_add():
    doc['div_emoji_list_from_html'].clear()
    p_msg=P("增加表符中...")
    doc['div_emoji_list_from_html']<=p_msg


#定義等待請求，一次增加所有被列出所選表符標籤的請求，再Table中顯示提示文字
def on_loading_adding_tag_to_all_emoji(res):
    for elt in doc.select('.span_adding_tag_msg'):
        elt.style.display="inline"

#定義完成請求，一次增加所有被列出所選表符標籤的，在Table中隱藏提示文字，並增加Tag的Span
def on_complete_adding_tag_to_all_emoji(res):
    for elt in doc.select('.span_adding_tag_msg'):
        elt.style.display="none"
    if res.status==200 or res.status==0:
        add_tag_list=doc['input_adding_tag_to_all_emoji'].value.split(",")
        doc['input_adding_tag_to_all_emoji'].value=""
        emoji_id_str_list=[img_emoji_elt.id[len("emoji_img"):] for img_emoji_elt in doc['div_emoji_list_from_html'].select('.emoji_pic')]
        for emoji_id_str in emoji_id_str_list:
            #尋找要加入標籤span的td區塊
            td_tag_list=doc['div_emoji_list_from_html'].select("#td_tag_list"+emoji_id_str)[0]
            for add_tag in add_tag_list:
                td_tag_list<=Span_tag(add_tag,emoji_id_str)
                #綁定新增的標籤事件:搜尋和刪除
                doc[emoji_id_str+"__tag__"+add_tag].bind("contextmenu",send_request_delelte_tag)
    else:
        alert('新增失敗 '+res.text)

#定義送出請求，一次增加所有被列出所選表符的標籤
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
    
#定義完成請求，一次增加所選表符的請求，置入已綁定的表符列表Table
def on_complete_send_confirm_selected_emoji_to_add(res):
    #清空之前的結果Table
    doc['div_emoji_list_from_html'].clear()
    #清空input的url和html內容
    doc['input_plurk_url'].value=""
    doc['input_plurk_html'].value=""
    if res.status==200 or res.status==0:
        if res.text[0]==u'沒':
            doc['div_emoji_list_from_html']<=P(res.text)
        else:
            emoji_dict_list=json.loads(res.text)
            table,showed_id_list,showed_tag_id_list=table_without_binding_and_showed_id_list_and_showed_tag_id_list(emoji_dict_list)
            doc['div_emoji_list_from_html']<=SPAN("新增全部標籤: ")+INPUT(type="text",id="input_adding_tag_to_all_emoji").bind("keyup",send_requset_adding_tag_to_all_emoji)+BUTTON("新增").bind("click",send_requset_adding_tag_to_all_emoji)
            doc['div_emoji_list_from_html']<=table
            #綁定table，但不綁定標籤搜尋，避免指定重複錯誤(不過刪除tag也會重複指定)
            binding_table(showed_id_list,showed_tag_id_list,click_tag_search=False)
            

#處理表符網址串列變成可視區塊列表，可選取和取消選取表符，附帶功能按鈕
def EmojiUrlList_to_divImgList(emoji_url_list):
    com_div=DIV()
    for emoji_url in emoji_url_list:
        img=IMG(src=emoji_url)
        com_div<=DIV(
            DIV(
                A(
                    img,
                    href="#!",
                ),
                Class="selected_emoji",
                style={
                    "width":"54px",
                    "height":"54px",
                },
            ).bind('mouseup',selecting_or_unselect_emoji),
            style={
                    "width":"56px",
                    "height":"56px",
                    "float":"left",
                    "margin-top":"0px",
            },            
        )
    btn1=BUTTON("全選",id="btn_select_all").bind('click',select_all_or_not)
    btn2=BUTTON("全不選",id="btn_unselect_all").bind('click',select_all_or_not)
    btn3=BUTTON("確定新增",id="btn_send_confirm_selected").bind('click',send_confirm_selected_emoji_to_add)
    return btn1+btn2+com_div+DIV(btn3,style={"clear":"both"})

#綁定事件，按下送出按鈕或者按下Enter，送出url或html來分析顯示所有噗文的表符圖片
@bind(doc['btn_send_inputed_plurk_url_or_html'],'click')
@bind(doc['input_plurk_url'],'keyup')
def send_inputed_plurk_url_or_htm(ev):
    if (ev.type=="keyup" and ev.keyCode==13) or (ev.type=="click"):
        doc['div_emoji_list_from_html'].clear()
        #輸入為噗文url的情況，則送出獲取原始碼的請求
        if doc['select_input_plurk_type'].value=="option_input_plurk_url":
            plurk_url=doc['input_plurk_url'].value
            #檢驗網址是否合法
            if "https://www.plurk.com" != plurk_url[:len("https://www.plurk.com")]:
                alert("網址不合法")
            else:
                send_request_PlurkUrlHtml(plurk_url)
         #輸入為原始碼的情況
        else:
            html_str=doc['input_plurk_html'].value
            emoji_url_list=getEmojiUrlListFromHtml(html_str)
            if emoji_url_list:
                divImgList=EmojiUrlList_to_divImgList(emoji_url_list)
                doc['div_emoji_list_from_html']<=divImgList
            else:
                doc['div_emoji_list_from_html']<=P("這則噗浪沒有表符")
    else:
        pass

#清空批量搜尋的input和Table
@bind(doc['btn_clear_inputed_plurk_url_or_html'],'click')
def clear_inputed_plurk_url_or_htm(ev):
    doc['input_plurk_html'].value=""
    doc['input_plurk_url'].value=""
    doc['div_emoji_list_from_html'].clear()


#定義送出請求，抓取url的原始碼
def send_request_PlurkUrlHtml(plurk_url):
    req = ajax.ajax()
    req.bind('loading',on_loading_PlurkUrlHtml)
    req.bind('complete',on_complete_PlurkUrlHtml)
    url=f'/PlurkEmojiHouse/PlurkUrlHtml?plurk_url={plurk_url}'
    req.open('GET',url,True)
    req.set_header('content-type','application/x-www-form-urlencoded')
    req.send()

#定義等待抓取url的原始碼，顯示提示訊息
def on_loading_PlurkUrlHtml():
    p_msg=P("分析噗文中...")
    doc['div_emoji_list_from_html']<=p_msg

#定義處理回應，顯示url的原始碼內的所有圖片，並可選取或取消選取表符，附帶功能按鈕
def on_complete_PlurkUrlHtml(res):
    doc['div_emoji_list_from_html'].clear()
    emoji_url_list=getEmojiUrlListFromHtml(res.text)
    if emoji_url_list:
        divImgList=EmojiUrlList_to_divImgList(emoji_url_list)
        doc['div_emoji_list_from_html']<=divImgList
    else:
        doc['div_emoji_list_from_html']<=P("這則噗浪沒有表符，或者此噗不公開，建議改用網頁原始碼新增表符")

