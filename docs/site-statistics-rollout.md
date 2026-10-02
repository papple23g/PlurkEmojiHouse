# 網站統計切換

- 累積數是頁面瀏覽次數，不是不重複訪客；每日訪客與來源由 GA4 管理。
- Firebase Auth 與使用者收藏 UID 保持原樣。前端不再讀寫 Firebase 計數。
- `POST /PlurkEmojiHouse/views` 需要 CSRF token，只遞增 1，忽略訪客傳入的總數。
- Django `/admin/myapp/siteviews/` 可查看 SQL 累積數、原始匯入值與匯入時間；欄位唯讀。

## 首次上線

1. 確認 Heroku 登入、目標 app `papple23g-mysite2`、現行 release 及資料庫備份。
2. 在短暫維護時段部署；Procfile release 階段先 migrate，再執行 `import_site_views`。
3. 匯入指令只讀 Firebase `PlurkEmojiHouse/WebSiteViews`，驗證整數後保存原值及時間。
4. 已存在 SQL 計數就略過，後續 release 不會重設；Firebase 讀取失敗會阻止首次 release。
5. 維護模式關閉後，驗證一個瀏覽增 1、搜尋不增加、後台基準及 Auth/收藏正常。

舊版已開啟的分頁仍可能寫回 Firebase；切換後 SQL 是唯一計數來源，不自動合併兩邊，以免重複計算。
累積數延續的是切換時快照，不宣稱修復舊版併發造成的歷史漏計。

## 故障／回復

計數 API 失敗時顯示「暫時無法取得」，搜尋維持可用，不切回 Firebase 雙寫。
回復上一版 Heroku release 前記錄 SQL 最新總數；不要刪除新表或重新匯入。
回復舊程式會恢復舊計數路徑；重新切換必須人工核對區間，不能把兩邊總數相加。

## GA4 與 AdSense

僅使用 papple12g@gmail.com。GA4 的新 measurement ID 必須由已建立的資源取得，不能預填假 ID。
AdSense 必須先核對帳戶 publisher ID，再替換舊代碼或新增 ads.txt；不以舊網站內的 ID 推定所有權。
