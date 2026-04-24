# 三種模式詳解

本 skill 提供三種風格化的解剖圖，各自對應 paopao 的教學情境。

-----

## `skeleton` — 骨架線稿

**用途**：步態分析、姿勢比較、投影片圖解、社群短圖卡。

**視覺風格**：
- 黑線白底
- 簡化為火柴人 + 主要骨骼結構
- 關節以圓點或小方塊標記
- 無陰影、無肌肉貼圖

**什麼時候挑這個**：
- paopao 要「比較擺盪期 vs 支撐期」
- paopao 想做「正確 vs 錯誤姿勢」對照
- 課程封面、單元標題圖
- 描述裡出現：骨架、線稿、步態、stick figure、簡化、輪廓

**Positive prompt 重點**：
`anatomical skeleton line drawing`, `stick-figure style with bone structure`,
`black lines on white background`, `gait analysis diagram`

**Negative prompt 重點**：禁止 photorealistic、color、muscle texture。

-----

## `muscle` — 肌肉解剖

**用途**：教材投影片、教科書風格插圖、單一肌群解說。

**視覺風格**：
- 彩色醫學插圖
- 半透明皮膚或剖面顯示深層肌肉
- 肌群可帶色彩分群（paopao 常用紅/橘強調目標肌群）
- 可標註肌肉名稱（Replicate 端的文字標註常失敗，建議後製）

**什麼時候挑這個**：
- 描述中提到具體肌肉：髖屈肌群、股四頭、豎脊肌、腓腸肌、比目魚肌
- 講解「哪條肌肉在哪個相位發力」
- 製作肌力課教材
- 關鍵字：肌肉、解剖、肌群、origin/insertion、力學

**Positive prompt 重點**：
`medical illustration of muscle anatomy`, `labeled muscle groups`,
`anatomical accuracy`, `textbook quality color illustration`

**Negative prompt 重點**：禁止 cartoon、chibi、deformed anatomy、wrong muscle placement。

-----

## `realistic` — 真人示範

**用途**：動作示範頁、社群貼文封面、課程宣傳素材。

**視覺風格**：
- 寫實攝影風格
- 中性健身房或 studio 背景
- 光線均勻，不戲劇化
- 人物比例正確，肌肉線條自然

**什麼時候挑這個**：
- paopao 想要「像真人 demo 的照片」
- 社群要發貼文、需要封面人像
- 關鍵字：真人、示範、動作、demo、寫實、照片

**Positive prompt 重點**：
`photorealistic human demonstration`, `athletic person performing the movement`,
`studio lighting`, `high resolution photograph`

**Negative prompt 重點**：禁止 cartoon、anime、illustration、painting、deformed body。

-----

## 模式判斷優先序（給 LLM）

使用者描述 → 對應模式：

1. **明說了就照做**：「骨架」→ skeleton，「肌肉」→ muscle，「真人」→ realistic
2. **含肌肉名詞** → `muscle`
3. **含「步態 / 相位 / 簡化 / 示意」** → `skeleton`
4. **含「示範 / 拍照 / demo」** → `realistic`
5. **都不明確** → **問 paopao**，不要猜

當 paopao 同一個姿勢要三種風格時，通常是用在教材的同一頁（左骨架、中肌肉、右真人）。
這種情境適合用 `batch_generate.py` 一次跑完。
