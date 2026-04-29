# 上頸椎 vs 中下頸椎 耦合動作對照（Cervical Coupling Demo）

「右側卡在伸直」推理流程的並列對照動畫：

- **左半邊**：C0-C1（同側耦合 / Ipsilateral）
- **右半邊**：C3-C4（對側耦合 / Contralateral）

用於 What's Up Anatomy 進階頸椎課程的學員自學與課堂示範。

---

## 開啟方式

不需要安裝任何東西，雙擊 `index.html` 用瀏覽器開啟即可（建議 Chrome / Edge / Safari 最新版）。

如果想在本機跑一個小伺服器（避免某些瀏覽器對 file:// 的限制），可以：

```bash
# Python 3
cd cervical-coupling-demo
python3 -m http.server 8000
# 然後到 http://localhost:8000
```

---

## 操作

| 動作 | 鍵盤 | 按鈕 |
|------|------|------|
| 下一步 | `→` | ⏭ |
| 上一步 | `←` | ⏮ |
| 自動播放 / 暫停 | `Space` | ▶️ / ⏸ |
| 重置 | `R` | 🔄 |
| 錄製 | — | 📹 |
| 切換中英 | — | 右上角「EN / 中」 |

兩邊的 3D 模型可以用滑鼠拖曳旋轉（OrbitControls），**左右視角會自動同步**，方便對照。滾輪可縮放。

---

## 5 步驟動畫腳本

| Step | 內容 |
|------|------|
| 0 · 起始 | 中立位。標示 C0-C1 的水平滑動軌道 vs C3-C4 的 45° 斜面軌道 |
| 1 · Extension | 兩邊頭部後仰，黃箭頭顯示左右 facet 的滑動方向 |
| 2 · 觸診發現 | 在 extension 位觸診 → 右側卡在前（紅色高亮 + 抖動） |
| 3 · 推回受限 | 嘗試 flexion → 右側不動 → 頭往左偏 |
| 4 · Coupling rule | 中央彈出警示橫幅；左右各跳出耦合規則卡片 |
| 5 · 結論 | C0-C1 走 SB Right + Rot Right；C3-C4 走 SB Right + Rot Left；底下出現對照表 |

---

## 錄製成課程影片

按 **📹 錄製** 按鈕後：

1. 介面進入錄製模式（隱藏所有控制 UI）
2. 自動從 Step 0 播放到 Step 5（總長約 30 秒）
3. 結束後瀏覽器自動下載 `cervical-coupling-<timestamp>.webm`
4. 解析度：**1920 × 1080 @ 30fps**，VP9 編碼

> **轉成 MP4**：webm 可直接放進 Premiere / Final Cut / DaVinci Resolve。如果課程平台只吃 mp4，用 ffmpeg 轉一下：
> ```bash
> ffmpeg -i cervical-coupling-xxx.webm -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p output.mp4
> ```

> **錄製範圍**：包含兩個 3D 視角 + 步驟說明 burn-in 文字 + 左右側標籤。為了讓影片獨立可看，文字是直接畫在合成 canvas 上而非用 DOM overlay，所以即使把影片放到別的播放器也不會掉字。

---

## 給 paopao 修改文字內容

所有可編輯的中英文都集中在 `index.html` 的 `i18n` 物件裡（搜尋 `const i18n =`）。

要改的東西大概這幾類：

- `desc[0..5]`：底部步驟說明文字
- `leftAnno[0..5]` / `rightAnno[0..5]`：每一步在左/右側畫面上的小註解框
- `leftRule` / `rightRule`：Step 4 出現的耦合規則大卡片
- `ipsiEasy` / `contraEasy`：Step 5 結論表格的「容易做的方向」

修改後直接重新整理瀏覽器即可看到效果，不需要 build。

> ⚠️ **paopao 要檢查的醫學細節**
>
> Step 5 結論目前寫成：
> - C0-C1：Extension + 右側彎 + 右旋轉
> - C3-C4：Extension + 右側彎 + 左旋轉
>
> 但「卡在前」在 C3-C4 是對應 extension 受限還是 flexion 受限，要看你課程怎麼定義 facet position。如果定義不同，請改 `desc[5]` / `leftAnno[5]` / `rightAnno[5]` / `ipsiEasy` / `contraEasy`。

---

## 下一步可擴充

要做別的節段對照（例如 C2-C3、T-spine），改這幾個地方：

1. `i18n` 物件：新增該節段的文字內容
2. `buildSpine(highlightLevel)` 函式：新增一個 `highlightLevel` 分支（例如 `'C23'`），在裡面呼叫 `pivotAt('C2')`
3. `buildStep(idx)` 裡的動畫：基本上 5 步流程一樣，只要把 `leftSpine.segments.C0` 改成新的 segment 名稱即可

骨頭幾何（`buildC0` / `buildC1` / `buildTypical`）已經夠通用，不需要改。

---

## 技術棧

- Three.js r128（CDN）
- GSAP 3.12（CDN）
- Tailwind CSS（CDN，僅用於 UI 排版）
- MediaRecorder API（錄製）
- 純 HTML / Vanilla JS — 沒有 build step、沒有 npm

檔案大小：單一 `index.html` < 40 KB（不含外部 CDN）。
