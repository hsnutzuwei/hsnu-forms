# 校外教學即時預覽驗收

此更新接續 PR #1 的 Word 修正（基準 `3cfe0f7660d8d59426872e06c8f4392b7cf38e98`），只改校外教學 Canvas 的即時填寫文字與字型載入後重繪。嵌入的原件底圖、全部 Word 輸出程式及資料、編輯欄位、草稿與地圖連結均未改。

## 修改前後

以下為 Chromium 實際 Canvas 的原生解析度截圖（1594 × 1124），資料與 Word 一般驗收案例相同，沒有以排版軟體重新製圖：

- [修改前](evidence/preview/before.png)
- [修改後](evidence/preview/after.png)
- [長文字案例](evidence/preview/long.png)
- [實際 Word 渲染，供位置對照](evidence/sample.png)

兩位教師分為左右兩欄；班級、科目、課表及調課採用 Word 寫入器相同的欄寬、直排容量與行距；修正日期、整點時間、星期及申請日期的位置；六種目的的黑方格對齊原方框。長文字改為分欄顯示，不再截取前 5／9／16 字。簽名欄留白。

## 字型及 Windows

填寫文字直接設定 Canvas `ctx.font`，字型依序為 DFKai-SB、標楷體、BiauKai、KaiTi、STKaiti、Noto Serif TC、Noto Serif CJK TC、PMingLiU、MingLiU、serif。Windows 瀏覽器可直接使用本機已安裝的 DFKai-SB，不需要下載字型。`document.fonts.ready` 與 `loadingdone` 會觸發校外教學重繪，避免字型較晚可用時仍停留在舊的替代字型畫面。

底圖的固定標籤維持原圖；本次字型設定作用於 Canvas 即時繪製的填寫文字，不更換原版固定文字或格線。

本環境是 Linux Chromium，未安裝真正的 Windows 標楷體。上述截圖顯示中文字型替代路徑，不能當成 Windows 原生標楷體的實測圖。自動測試另以本機 Noto Sans CJK TC 建立名為 DFKai-SB 的測試字型，確認第一順位字型載入後，Canvas 確實重繪且像素改變；此測試只驗證字型選用與重繪流程，不宣稱驗證真正的標楷體字形。

Windows 最後確認：在安裝標楷體的電腦以 Edge／Chrome 開啟本分支網頁，輸入陳小明、林小華、美術及民國 115/11/12，確認預覽採用標楷體、雙教師分欄、兩聯星期四及日期對齊；再與下載 Word 對照。瀏覽器若因個別設定封鎖本機字型，則使用列出的中文字型替代，不中斷預覽。

## 已通過的檢查

```sh
python tests/check_fieldtrip_preview.py --browser /usr/bin/chromium --output-dir work/preview-check
python tests/check_fieldtrip_word.py --browser /usr/bin/chromium --output-dir work/word-check
```

- 預覽專用區域以外的 index.html 原始碼與基準完全一致。
- 四種表單實際下載的 DOCX，ZIP 內各檔案內容與基準逐一完全相同，包含校外教學。
- 另外三張表單的 Canvas PNG 與基準逐像素相同。
- Canvas 的所有即時填寫文字均將 DFKai-SB 列為第一順位；無標楷體時中文字仍可繪製。
- 模擬本機第一順位字型載入後自動重繪，實際 Canvas 像素改變。
- 最長教師、地點、課表及其他說明已截圖並目視檢查；沒有截字或新增溢出。
- 草稿儲存及載入通過，原有 Word 驗收測試通過。

不合併 main，不部署網站。
