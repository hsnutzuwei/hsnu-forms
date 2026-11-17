# 入校申請備註、14pt 文字與選填簽核資訊驗收

本次只調整入校申請；基準為正式版 main `994609992b75af78d7a359d1aaa5f2775adc66c5`。

## 修改

- 備註改為較寬的多行輸入欄。桌面固定欄寬，手機以每人一張直向卡片顯示日期、姓名、備註，完整顯示備註欄，無須左右捲動尋找。
- Word 日期、姓名、備註資料全部指定標楷體 14 pt；維持原 A4 直式及 19 列。資料列固定 31 pt，文字行距 14.5 pt，長姓名與備註可佔兩行，備註沿用最多 25 字。
- 承辦人與單位主管各有選填姓名、日期，日期輸出為民國年。填寫資訊列在原簽章欄下方；原「承辦人：」「單位主管：」段落及空白蓋章位置不替換。各欄未填就不輸出該欄的姓名／日期標籤，全部未填時不新增資訊段落。
- 保留新舊 JSON 草稿、原美術班落款右對齊；移除原件尾端多餘空白段落，避免出現第二張空白頁。
- Canvas 即時預覽同步 14pt、31pt 列高與選填簽核資訊；其他三張表單不變。

## 實際檢查

以 Chromium 的 390 × 844 手機尺寸實際填入 19 列資料、輸入備註、下載 Word、儲存／清空／載入 JSON 草稿，再以 LibreOfficeDev 26.8 轉檔渲染，已目視檢查全頁。

| 案例 | 輸出結果 |
| --- | --- |
| 一般資料、兩位簽核姓名及日期 | A4 單頁 |
| 19 列全填，每列 16 字姓名、25 字備註，兩位簽核資訊完整 | A4 單頁、兩行文字無裁切或重疊 |
| 空白表單、不填簽核欄 | A4 單頁、不產生新的「姓名：」「日期：」文字 |
| 只填承辦人姓名，不填其他簽核欄 | A4 單頁、只顯示有填的姓名 |
| 舊草稿（只有 rows） | 正常載入及下載，A4 單頁 |

五種案例的實際 PDF 均只有一頁，尺寸 595.304 × 841.890 pt。一般及最滿案例，PDF 中表格資料文字字級逐一檢查均為 14.0 pt；DOCX 對應 w:sz=28。手機備註欄實測至少 280 CSS px 且完全位於 390px 視窗內。

`tests/check_entry_readability.py` 已通過：手機實際輸入與可見範圍、57 格填寫文字字級、新舊草稿、選填／不填行為、19 列保留。其他三張表單更新前後實際 DOCX 的 ZIP 各檔內容逐一相同，Canvas PNG 逐像素相同。`git diff --check` 通過。

```sh
python tests/check_entry_readability.py --browser /usr/bin/chromium --output-dir work/entry-check
```

輸出的 Word 需再以 Word 或 LibreOffice 渲染檢查頁數與位置。本環境沒有 Windows 標楷體，渲染使用中文字型替代；DOCX 仍指定標楷體，Windows Word 的實際字形可再由使用者確認。

## 文件與截圖

- [一般填寫 Word](evidence/entry-readable/entry-normal.docx)／[實際渲染](evidence/entry-readable/word-normal.png)
- [最滿案例 Word](evidence/entry-readable/entry-full.docx)／[實際渲染](evidence/entry-readable/word-full.png)
- [空白表單渲染](evidence/entry-readable/word-empty.png)
- [手機備註輸入卡片](evidence/entry-readable/mobile-remarks.png)
- [即時預覽](evidence/entry-readable/preview.png)

測試文件使用虛構姓名及備註。本分支供確認，尚未合併或部署。
