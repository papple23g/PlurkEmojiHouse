
#定義動作:進行登入
def login():
	#定義動作:使用者登入引導
	def newLoginHappened(user):
		#若目前使用者存在(即已經登入)，則執行登入後的動作
		if user:
			pass
		#若使用者還沒登入，就使用Google提供商的登入介面進行登入
		else:
			provider=firebase.auth.GoogleAuthProvider.new()
			firebase.auth().signInWithPopup(provider)
	
	#獲取使用狀態並進行引導
	firebase.auth().onAuthStateChanged(newLoginHappened)

#定義動作:登出
def SingOut(ev):
	confirm_to_signOut=confirm("確定要登出嗎?")
	if confirm_to_signOut:
		firebase.auth().signOut()
	else:
		pass

#定義頁面DIV元素，會因為登入狀態而改變內容
def DIV_login():
	div_elt=DIV()
	if window.firebase.auth().currentUser:
		user=window.firebase.auth().currentUser
		div_elt<=IMG(
			src=user.photoURL,
			style={
				'width':'30px',
				'border-radius':'30px',
			},
		)
		div_elt<=SPAN(" "+user.displayName)
		div_elt.bind('click',SingOut)
	else:
		div_elt<=IMG(src="https://icon-library.net/images/anonymous-icon/anonymous-icon-0.jpg",style={'width':'30px'})
		div_elt<=I(Class="fab fa-google",style={'margin':'0 5px'})
		div_elt<=SPAN("登入")
		div_elt.bind('click',lambda ev:login())
	return div_elt

#定義動作:當載入網站或登入狀態有變動時，就刷新登入DIV元素，以及刷新搜尋結果
def onAuthStateChanged(user):
    #刷新登入DIV元素
	doc['DIV_userLoginInfo'].clear()
	doc['DIV_userLoginInfo']<=DIV_login()
	#若為登入動作:顯示顯示我的收藏勾選元素
	if window.firebase.auth().currentUser:
		doc['div_showCollectEmojis'].classList.remove("disabled")
		doc['checkbox_showCollectEmojis'].disabled=False
	#若為登出動作:關閉顯示我的收藏勾選元素並取消勾選
	else:
		doc['div_showCollectEmojis'].classList.add("disabled")
		doc['checkbox_showCollectEmojis'].disabled=True
		doc['checkbox_showCollectEmojis'].checked=False
	#刷新搜尋結果
	doc['search_tag_btn'].click()
firebase.auth().onAuthStateChanged(onAuthStateChanged)

