# Website downtime for Plurk Emoji House
_Exported on 2026/4/18 at 23:01:11 [GMT+8] from Cursor (3.2.0-pre.24.patch.0)_

---

**User**

我網站又掛了https://papple23g-mysite2.herokuapp.com/PlurkEmojiHouse
@c:\Users\pappl\.cursor\projects\c-Users-pappl-Github-Django-projects-plurkEmojiHouse-papple23g-mysite2\terminals\1.txt:165-263  /1

---

**Cursor**

分析 Heroku H12（30 秒請求逾時）並檢視專案中可能導致阻塞的路由與設定。正在搜尋官方說明並讀取程式碼。



主頁 `PlurkEmojiHouse` 僅為 `render`，但日誌顯示連 `/favicon.ico` 也逾時，可能為 worker 耗盡、資料庫連線阻塞或 dyno 層級問題。繼續檢查設定與其他 view。



已確認：`HashOfImage_inputUrl` 的 `requests.get` 未設 `timeout`，可能長時間阻塞 worker；`Procfile` 未載入 `gunicorn.conf.py`；生產環境使用 `conn_max_age=600`，在 Heroku 上易造成連線問題。



---

**User**

請盡可能做幾個必要且重大的調整就好，我怕調整太多引發更多BUG
修完就測試 + push 到 heroku
/sequential-thinking

---

**Cursor**

採用 sequential thinking：先處理會無限期阻塞 worker 的 HTTP 請求（最高風險／最小改動），再修正 Heroku 上易導致連線卡死的 `conn_max_age`，最後讓 Gunicorn 載入既有 `gunicorn.conf.py` 以套用 `timeout=20`。接著執行測試並 push 到 Heroku。



實作三項變更：(1) 圖片下載加 `timeout`，避免 worker 無限阻塞；(2) `conn_max_age=0`，降低 Heroku Postgres 僵屍連線；(3) `Procfile` 改為載入 `gunicorn.conf.py`，並將 `workers` 轉成整數。



6 項測試皆通過。正在提交並推送到 Heroku。



以下用 **sequential thinking** 簡述決策，並說明已做的最小變更與結果。

## 推理鏈（精簡）

1. **現象**：H12 = 30 秒內沒有 HTTP 回應；連 `/`、favicon 都掛，代表多半是 **worker 被占滿** 或 **DB/HTTP 卡死**，不是單一模板問題。\
2. **最高槓桿、最少程式面積**：先消掉「**沒有 timeout 的對外 HTTP**」與「**Heroku 上長壽 DB 連線**」，這兩類最常在生產環境造成整站假死。\
3. **刻意不做**：大改 `search_by_tag` 的 `__hash__` 全表掃描、COUNT 快取、`PlurkUrlHtml` 總時間預算等——避免你擔心的一波 refactor 帶來新 bug。

## 已做的 4 處修改

| 檔案 | 變更 |
|------|------|
| [`myapp/models.py`](myapp/models.py) | `HashOfImage_inputUrl` 的 `req.get` 加上 **`timeout=12`**，避免圖片網址卡住時占死 worker。 |
| [`mysite2/settings.py`](mysite2/settings.py) | 有 `DATABASE_URL` 時 **`conn_max_age=0`**，降低拿到已失效 Postgres 連線而整站掛死的機率。 |
| [`Procfile`](Procfile) | 改為 **`gunicorn mysite2.wsgi -c gunicorn.conf.py`**，讓實際生效的 **`timeout=20`**、`gthread`、`threads=4` 等設定被用上（先前 Procfile 等於沒吃到這份設定）。 |
| [`gunicorn.conf.py`](gunicorn.conf.py) | `workers` 改為 **`int(os.environ.get("WEB_CONCURRENCY", "2"))`**，避免環境變數是字串時行為曖昧。 |

## 測試與部署

- **`uv run pytest`**：6 passed（含整合測試）。\
- **`git push heroku master`**：已發佈 **v146**。\
- 部署後 **`curl` `/PlurkEmojiHouse`**：約 **1.6s** 回 **200**。

若之後仍偶發 H12，下一步才需要動到較大的查詢／`PlurkUrlHtml` 迴圈上限；有需要再說即可。若要同步到 GitHub，可執行 `git push origin master`（此次我只推了 Heroku）。

---

**User**

請調查這網站什麼時候開始掛掉的?

---

**Cursor**

正在從本機可取得的紀錄（終端機日誌、git 部署歷史）調查；若需精確的 Heroku 首發時間，會嘗試用 Heroku CLI 查 release 紀錄。



根據你本機終端機裡的 `heroku logs --tail` 緩衝、以及剛查到的 **Heroku releases**，結論如下。

## 什麼時候開始「看起來掛掉」（H12）？

在目前這份 log 裡，**最早一筆** Heroku 路由器回報的 **H12（Request timeout）** 時間是：

- **`2026-04-18T11:25:07+00:00`（UTC）**\
- 換成 **台灣時間（UTC+8）**：**2026-04-18 19:25:07**

也就是從你開始 `heroku logs --tail` 之後，緩衝區裡能看到的 **第一個** 全站型逾時（先是 `GET /`，接著 `favicon.ico` 等）。

之後同一天一路都有斷斷續續的 H12，直到 **修復版 v146 部署、web dyno 重啟** 後，同一個 log 裡才出現 **`GET /PlurkEmojiHouse` 約 19ms、`200`**（例如 `2026-04-18T14:48:28Z` 那筆）。

---

## 不能從現有資料「斷定」的範圍

- 這份紀錄 **只涵蓋你執行 `heroku logs --tail` 的那段時間**，**無法**由此推論 **4/18 19:25（台灣）之前**是否已經在掛（更早的 log 沒在這個檔案裡）。
- 若要知道「第一次出事」是否在更早的日期，需要你在本機執行例如：\
  `heroku logs -a papple23g-mysite2 -n 1500`\
  或加 **Log 附加元件／付費保留期** 才查得到更久以前的 router log。

---

## 和「上次上線」的關係（releases）

Heroku 上 **這次出事前最後一次程式部署**是：

- **v145**：`2026/03/27 10:18:09 +0800`（commit `83046d5`）

也就是說：**3/27 到 4/18 之間沒有新的 release**，但 **4/18 當天**仍出現大量 H12。這比較像 **運行中狀態**（連線、併發、外部請求、資料量等）惡化，而不一定是「4/18 當天才 deploy 壞掉」；當然也不能排除 **3/27 那版在特定負載下**才會觸發問題。

---

**一句話**：依你現有的 log，**能指認的「開始大量 H12」不早於 `2026-04-18 19:25（台灣時間）`**；**約在當天 `22:48（台灣時間）` v146 上線後**已回到正常 **200**。若要精準到更早的「第一次掛」時間，需要拉更長的 Heroku log 歷史。
