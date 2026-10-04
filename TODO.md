# 待辦事項

## 2026-10-05：既有 CRUD、安全與錯誤處理問題

以下六項在發布前補測中重現，屬既有問題，並非本次廣告版面與懸浮說明新增的缺陷。狀態皆為待修復。

- 驗證版本：`codex/plurk-upgrade`，`afcb886de28cd38cccf8b1b8e3b06686653170ee`。
- 比對的正式來源：Heroku Git `master`，`86bc77325769578ef30bb65aea4948c9dec8196f`。
- 測試環境：Python 3.12.14、Django 5.2.17、本機隔離 PostgreSQL 17.9；未對正式資料庫執行寫入測試。
- 正常功能：既有 91 項與新增 CRUD 8 項通過；另有 1 項組合新增成功回呼契約測試通過。
- 缺陷證據：8 項後端權限／異常測試、3 項前端異常回呼測試失敗，合併為下列六項；失敗案例數不等於獨立問題數。
- 優先級：P1 優先處理安全與資料完整性；P2 處理併發、重試及錯誤回復。

### P1-01：收藏操作缺少身分與所有權驗證

- [ ] 修復收藏操作的後端驗證。

**重現：** 匿名請求可新增或刪除另一個 UID 的 `__collectorUsers__` 收藏標籤，回應 200 並確實改變資料。前端登入檢查無法保護後端端點。

**位置：** `myapp/views.py` 的 `emoji_add_tag`、`delete_tag`。

**修正方向：** 後端驗證 Firebase 登入憑證，從已驗證身分決定收藏 UID；限制使用者只能修改自己的收藏。修改操作改用 POST，並依登入憑證傳遞方式加入適當的 CSRF 防護。

**驗收：** 匿名、無效／過期憑證、偽造他人 UID 均不能改變收藏；合法使用者可增刪自己的收藏，公開搜尋仍不輸出收藏識別標記。

**重現案例：** `test_anonymous_cannot_modify_another_users_favorite`、`test_anonymous_cannot_delete_another_users_favorite`。

### P1-02：圖片與噗文匯入來源可繞過限制（SSRF）

- [ ] 對匯入網址及重新導向建立來源限制。

**重現：** 圖片網址只要包含 Plurk 網址字串，即可通過檢查；噗文匯入直接使用傳入網址。測試確認非 Plurk／內網網址會送往下載函式，網路呼叫由 mock 攔截，未實際連線內網。

**位置：** `myapp/views.py` 的 `search_by_url`、`search_by_url_list`、`PlurkUrlHtml`；`myapp/models.py` 的 `HashOfImage_inputUrl`。

**修正方向：** 解析 URL 並驗證 scheme、實際 hostname 與允許來源，拒絕內網目標；重新導向的每一跳也須通過驗證，不使用字串包含判斷來源。

**驗收：** 非允許主機、偽裝網址與導向內網的請求被拒絕，不下載目標、不建立資料；合法 PNG／GIF、噗文及批次匯入仍可使用。

**重現案例：** `test_image_import_rejects_non_plurk_host_before_fetch`、`test_plurk_import_rejects_non_plurk_host_before_fetch`。

### P1-03：批次新增標籤失敗後留下部分修改

- [ ] 讓批次標籤操作具有整批成功或整批回復的行為。

**重現：** 傳入一個有效 ID 與一個不存在 ID，回應 500，但第一個表符已新增標籤。

**位置：** `myapp/views.py` 的 `emoji_list_add_tag`。

**修正方向：** 先驗證全部 ID 與標籤參數，再以資料庫交易完成整批寫入；無效輸入回受控錯誤。

**驗收：** 任一 ID 不存在或任一步驟失敗時，所有表符及標籤關聯維持操作前狀態；正常批次與重複送出不產生重複關聯。

**重現案例：** `test_batch_tag_failure_leaves_no_partial_write`。

### P2-01：重複刪除會回應 500

- [ ] 讓刪除標籤與組合表符可以安全重試。

**重現：** 第一次刪除成功；第二次刪除同一標籤或組合表符，分別因資料不存在及索引越界回應 500。

**位置：** `myapp/views.py` 的 `delete_tag`、`DeleteCombindEmoji`。

**修正方向：** 明確處理已刪除／不存在資料，回傳一致的受控結果，避免直接取不存在的標籤或查詢結果首筆。

**驗收：** 連續刪除、兩個頁面同時刪除及不存在目標均不回 500、不影響其他表符的關聯；刪除結果可供前端正常回復。

**重現案例：** `test_repeated_delete_is_controlled[False]`、`test_repeated_delete_is_controlled[True]`。

### P2-02：同時匯入相同網址會建立重複表符

- [ ] 建立併發安全的表符匯入與網址唯一性約束。

**重現：** 兩個請求同時查到網址不存在，接著都新增成功，回應均為 200，但同一網址建立兩筆 Emoji。循序重複匯入通過測試，不代表併發情境安全。

**位置：** `myapp/views.py` 的 `search_by_url`、`search_by_url_list`；`myapp/models.py` 的 `Emoji.url`。

**修正方向：** 先盤點既有重複網址，保留並整併全部標籤、收藏與相關關聯，再建立資料庫唯一限制與併發安全的新增流程。不得直接刪除重複列；migration 必須先在還原 PostgreSQL 副本驗證。

**驗收：** 併發及批次重試最後只保留一筆同網址資料；歷史整併不遺失公開標籤、收藏或組合關係，並驗證舊程式回復相容性。

**重現案例：** `test_concurrent_image_import_preserves_unique_url`。

### P2-03：前端未處理斷線、空回應與非 JSON 錯誤

- [ ] 統一相似標籤、批次表符新增及組合表符新增的失敗處理。

**重現：** 相似標籤收到 500 HTML 時拋出 `JSONDecodeError`；批次表符新增收到 status 0 空回應時拋出 `IndexError`；組合新增收到相同空回應時拋出 `JSONDecodeError`。

**位置：** `templates/request_function.py` 的 `SendRequest_searchTags`、`SendRequest_addEmojiList`、`SendRequest_addCombindEmoji`。

**修正方向：** 檢查 HTTP 狀態、空內容與解析結果；status 0 不視為成功。失敗時提供可重試提示、結束等待狀態並恢復按鈕，保留既有搜尋回應順序保護。

**驗收：** 斷線、逾時、空回應、HTML 錯誤與不符格式的 JSON 都不拋出未處理例外；操作可重試、按鈕恢復；成功與過期回應行為不退步。

**重現案例：** `test_actual_registered_callback_handles_failure` 的三組參數。須透過父函式實際註冊的 callback 測試；直接抽取巢狀函式會遺失 closure，不能把測試框架的 `NameError` 誤列為應用程式缺陷。

## 尚未完成的操作驗收

以下是驗收缺口，並非已確認的程式缺陷。

- [ ] 使用真實 Google／Firebase 登入，在瀏覽器驗證表符新增、標籤修改、收藏增刪與組合表符操作；本機 Firebase stub 不能作為登入證據。
- [ ] 在 DESKTOP-P80HOL8 的實際工作樹驗收；筆電上的結果不能取代桌機實測。
- [ ] 修復後將工作樹外的重現案例納入專案測試，重跑既有套件、全部失敗案例及瀏覽器流程，再記錄發布判定。

## 證據索引

完整紀錄為 Codex 任務 `codex-01a0ebca-12df-7321-9f8a-a9e486060b1e` 的 `outputs/發布前CRUD驗收-20261005.md`。下列檔案目前位於該任務的 `outputs/work`，未納入本 repository：

| 證據 | 結果／用途 |
|---|---|
| `release-full-pg-20261005.xml` | 91 passed，包含外部 Plurk、PostgreSQL UTC 與 32 次計數併發。 |
| `test_release_crud.py`、`release-crud-pg-20261005.xml` | 新增 CRUD 補測 8 passed，含管理後台完整增查改刪。 |
| `release-boundaries-pg-20261005.xml` | 後端權限／異常案例 8 failed。案例來源為原升級任務工作目錄的 `upgrade-review/test_upgrade_review.py`。 |
| `test_release_callbacks.py`、`release-callbacks-verified-20261005.xml` | 修正測試框架後，前端異常回呼 3 failed。 |
| `release-baseline-comparison-20261005.json` | 主要失敗函式與正式版本的 AST 比較。相似標籤回呼雖新增過期回應保護，未處理錯誤解析的邏輯仍沿用正式版。 |
