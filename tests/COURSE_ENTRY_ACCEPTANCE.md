# 教師請假字級與入校落款對齊驗收

基準為已部署的 main `2ac8ef7a3871f073f5670f1cc58dfe1d4ae5f140`；本次使用獨立分支，不部署正式網站。

## 修改及實際輸出

教師請假 Word 學年度由 9.5 點放大為 18 點，與標題字級一致；備註列「擬請＿＿教師代理導師」的教師姓名由 9 點放大為 12 點，兩側各保留兩個全形空白。依使用者明確回覆，增加的是代理教師姓名前後的空間，不改上方姓名欄或表格欄寬。右側備註文字增加 12 點左縮排。

教師請假預覽將完整灰底說明放在標題下一行，並同步顯示放大的學年度、代理教師及備註位置；填表日期靠右。底圖、格線及 Word 固定文字未改。

入校申請 Word 的「美術班115.3.」依紙張內文寬度與置中表格寬度計算右縮排（353 twips = 17.65 點），對齊表格右邊線；預覽同步右對齊。入校的其他文字、格線、姓名及日期欄位不改。

| 項目 | 修改前 | 修改後 |
| --- | --- | --- |
| 教師請假 Word | [渲染](evidence/course-entry/course-word-before.png) | [渲染](evidence/course-entry/course-word-after.png) |
| 教師請假網站預覽 | [Canvas 截圖](evidence/course-entry/course-preview-before.png) | [Canvas 截圖](evidence/course-entry/course-preview-after.png) |
| 入校申請 Word | [渲染](evidence/course-entry/entry-word-before.png) | [渲染](evidence/course-entry/entry-word-after.png) |

可下載：[教師請假測試 DOCX](evidence/course-entry/course.docx)、[入校申請測試 DOCX](evidence/course-entry/entry.docx)。另有 [12 字教師、50 字備註及 10 列課程的測試渲染](evidence/course-entry/course-long.png)、[入校預覽](evidence/course-entry/entry-preview-after.png)。以上均使用虛構資料。

## 驗收結果

以 Chromium 實際填表及按下載按鈕，產生修改前後 DOCX，再以 LibreOfficeDev 26.8 轉檔並渲染全頁檢查。一般教師請假、長文字教師請假、入校申請均單頁，無新增文字重疊；渲染 PDF 的影像物件數均為 0，DOCX 保留原生可編輯文字與表格。

實際 PDF 座標比較（pt）：

- 學年度字級 9.5 → 18。
- 代理教師「王小明」字級 9 → 12，文字左右邊界 170.10–206.10；左右各 24 點空白，與「擬請」及「教師代理導師」分開。
- 備註文字左端 577.05 → 589.05，向右移 12 點。
- 入校表格右邊線 x=535.10，落款文字右端 x=535.253（字型渲染邊界誤差約 0.153 點）。表格本身位置未變。

自動測試：

```sh
python tests/check_course_entry_layout.py --browser /usr/bin/chromium --output-dir work/course-entry-check
```

通過：指定字級、代理教師兩側空白、備註縮排、入校只改落款縮排、校外教學與外賓停車的 DOCX 各 ZIP 檔內容完全相同且 Canvas PNG 逐像素相同；教師請假與校外教學的 JSON 草稿儲存／清空／載入後資料正常還原；最長代理教師及備註和 10 列課程已輸出及渲染檢查。`git diff --check` 通過。

環境沒有真正的 Windows 標楷體，渲染使用中文字型替代；DOCX 仍指定標楷體，建議於安裝標楷體的電腦版 Word 最後確認外觀。

## 草稿使用方式

「儲存草稿」下載目前表單的 JSON，通常存到瀏覽器的「下載」資料夾；「載入草稿」選擇這個 `.json` 檔案，會自動切換到對應表單並還原。Word 下載不會自動產生草稿，Word 檔也不能當作 JSON 草稿載入。本次未更動草稿功能。
