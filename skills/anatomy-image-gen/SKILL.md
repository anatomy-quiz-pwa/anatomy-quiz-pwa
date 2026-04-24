---
name: anatomy-image-gen
description: Paopao 的解剖圖自動生成 Skill。輸入姿勢參考照片 + 中文描述，自動透過 Replicate API 生成三種風格的解剖圖：骨架線稿（skeleton，步態分析用）、肌肉解剖（muscle，教材投影片用）、真人示範（realistic，動作示範用）。支援批次模式（一次幾十張，Telegram 通知完成）。觸發關鍵字：生成解剖圖、做解剖圖、解剖示意、anatomy image、骨架圖、肌肉示意、姿勢圖、anatomy-image-gen、我要一張解剖圖、把這張照片變成骨架圖、做步態分析圖、做教材圖、批次生成解剖圖。即使使用者只說「把這張照片變成解剖風格」或「幫我生一張骨架線稿」也應立即觸發。當 slide-maker 或 course-mode 需要補圖時也應觸發。
---

# anatomy-image-gen

Paopao 的半自動解剖圖生成工具。paopao 不需要碰 ComfyUI、也不需要手寫 prompt，只要給
一張姿勢參考照 + 一句中文描述，就能產出 Boneman 品牌風格的解剖教學圖。

-----

## 1. 何時觸發（Trigger Conditions）

立即觸發本 skill 的情境：

- paopao 直接說：「幫我生成解剖圖 / 做一張骨架圖 / 做肌肉示意圖 / 做動作示範圖」
- paopao 附上照片並說「把這張變成解剖風格 / 變骨架線稿 / 變肌肉解剖」
- paopao 提到「步態分析圖」「擺盪期」「支撐期」需要示意圖
- paopao 給一份 CSV 說要「批次生成」
- 其他 skill（`slide-maker` / `course-mode`）在製作教材時標註「此處需要解剖圖」
- 關鍵字：生成解剖圖、做解剖圖、解剖示意、anatomy image、骨架圖、肌肉示意、姿勢圖

只要使用者語意指向「產出一張醫學/解剖/姿勢的示意圖」，即使沒明說 skill 名稱，也要觸發。

-----

## 2. 三種模式（Mode Selection）

完整說明見 `references/modes.md`。快速判斷：

| 模式 | 關鍵詞 | 用途 |
|------|--------|------|
| `skeleton` | 骨架、線稿、步態、stick figure、輪廓、簡化 | 步態分析、姿勢比較、投影片圖解 |
| `muscle` | 肌肉、解剖、肌群、髖屈肌、股四頭、肌肉圖 | 教材投影片、教科書風格醫學插圖 |
| `realistic` | 真人、示範、動作、demo、寫實 | 動作示範頁、社群貼文封面 |

**判斷優先順序**：
1. paopao 明確指定 → 用他說的
2. 描述中含肌肉名詞 → `muscle`
3. 描述中含「步態 / 線稿 / 簡化」→ `skeleton`
4. 描述中含「示範 / 寫實 / 真人」→ `realistic`
5. 都沒有 → **問 paopao**，不要自己猜

-----

## 3. 單張生成流程（Single Generation）

使用者提供：參考圖路徑 + 中文描述 + 模式（可選）。

```bash
python scripts/generate.py \
    --reference /path/to/pose.jpg \
    --description "側面視角，顯示髖屈肌群，跑步擺盪期" \
    --mode muscle \
    --output-dir ~/Boneman/generated
```

內部流程：

1. 驗證參考圖存在且副檔名為 `.jpg/.jpeg/.png/.webp`
2. 呼叫 `prompt_builder.build_prompt(chinese, mode)` 產生英文正/負 prompt
   - 會嘗試串接 `/mnt/skills/user/boneman-style/` 的邏輯
   - 若該 skill 不在，退回內建的 Boneman 風格關鍵字模板
3. 呼叫 `replicate_client.run(model, inputs)` 送到 Replicate
4. 下載結果到 `output_dir`
5. 檔名：`{YYYY-MM-DD_HHMMSS}_{mode}_{short-desc-slug}.png`
6. 同時存 `.json` metadata：`prompt` / `negative_prompt` / `model` / `seed` /
   `reference_image` / `mode` / `timestamp` / `cost_usd`

若 `REPLICATE_API_TOKEN` 未設定，`generate.py` 會進入 **dry-run 模式**：
只印出完整 prompt 與預計呼叫的模型，不實際送出 API。適合 Phase 1 測試。

-----

## 4. 批次生成流程（Batch Generation）

讀取 CSV（範本在 `assets/batch_template.csv`）：

```csv
reference_image,mode,description,output_name
./refs/gait_swing.jpg,skeleton,跑步擺盪期側面骨架,gait_01
./refs/gait_swing.jpg,muscle,跑步擺盪期髖屈肌群,gait_01_muscle
./refs/squat.jpg,realistic,深蹲最低點側面,squat_demo
```

執行：

```bash
python scripts/batch_generate.py \
    --csv ./batch.csv \
    --output-dir ~/Boneman/generated/2026-04-24_batch \
    --notify-every 5
```

行為：

- **序列執行**（非並行），避免 Replicate rate limit
- 每完成 `--notify-every` 張呼叫一次 `telegram-notify`（若可用）
- 失敗的列記到 `errors.csv`，繼續跑剩下的，**不要中斷整批**
- 結束時輸出總結：成功 / 失敗 / 總花費 USD

-----

## 5. 與其他 Skill 的整合

- **boneman-style**：`prompt_builder` 會優先嘗試 import 或呼叫
  `/mnt/skills/user/boneman-style/`。若找不到，使用內建備援模板。
- **telegram-notify**：批次模式每 N 張 / 結束時，若 `~/.config/telegram-notify/`
  或對應 skill 存在，就呼叫；否則只印到 stdout。
- **slide-maker / course-mode**：這兩個 skill 可以直接呼叫本 skill 的 CLI，
  參數同「單張生成流程」一節。**設計時一律假設被其他 skill 呼叫**——
  不要用互動式 prompt，所有輸入走 CLI flag 或檔案。

-----

## 6. 錯誤處理

| 情境 | 行為 |
|------|------|
| `REPLICATE_API_TOKEN` 未設定 | 進入 dry-run，印出 prompt 並提示去 https://replicate.com/account/api-tokens 申請 |
| 參考圖不存在 / 格式不支援 | 立刻報錯，不浪費 API 額度 |
| Replicate API 回 429 / 5xx | `replicate_client` 自動 retry 3 次（exp backoff：2s/4s/8s）|
| Replicate 回 402（額度不足）| 立刻中止，提醒 paopao 儲值 |
| 批次中單張失敗 | 記錄到 `errors.csv`，繼續下一張 |
| 中文翻譯失敗（無 ANTHROPIC_API_KEY） | 退回內建英文關鍵字模板，不中斷 |

-----

## 7. 輸出結構

預設輸出到 `~/Boneman/generated/`（paopao 是 Mac，習慣路徑）：

```
~/Boneman/generated/
├── 2026-04-24_143022_muscle_hip-flexor-swing.png
├── 2026-04-24_143022_muscle_hip-flexor-swing.json
└── 2026-04-24_batch/
    ├── gait_01.png
    ├── gait_01.json
    ├── gait_01_muscle.png
    ├── gait_01_muscle.json
    └── errors.csv            # 只在有失敗時才產生
```

每張圖的 JSON metadata 範例：

```json
{
  "prompt": "side view anatomical illustration, hip flexor muscles highlighted, ...",
  "negative_prompt": "cartoon, low quality, deformed anatomy, ...",
  "model": "stability-ai/sdxl",
  "model_version": "7762fd07...",
  "seed": 42,
  "reference_image": "/Users/paopao/refs/gait_swing.jpg",
  "mode": "muscle",
  "timestamp": "2026-04-24T14:30:22+08:00",
  "cost_usd": 0.018
}
```

-----

## 8. Phase 狀態

- **Phase 1（已完成，可離線測試）**：SKILL.md、prompt_builder、CLI 骨架、
  CSV 讀取、references 文件、dry-run 模式
- **Phase 2（等 paopao 申請 Replicate token 後）**：實際 API 呼叫、微調 prompt、
  Telegram 整合、第一張真實測試圖
- **Phase 3（進階）**：與 slide-maker 深度整合、自動入庫 Boneman 素材、
  同課程風格一致性檢查

paopao 申請 Replicate token 步驟：
1. 打開 https://replicate.com → 用 GitHub 登入
2. 右上角頭像 → Account settings → **API tokens**
3. 建立新 token，複製
4. Mac 上執行：`echo 'export REPLICATE_API_TOKEN=r8_xxx' >> ~/.zshrc && source ~/.zshrc`
   或存到 `~/.config/replicate/token`

-----

## 9. 設計原則（給未來維護者的提醒）

- **不要寫死模型名稱**：改 `references/replicate_models.md`
- **不要寫死 prompt 模板**：改 `scripts/prompt_builder.py` 的常數區塊
- **API key 不入版控**：使用環境變數或 `~/.config/replicate/token`
- **大圖別塞進 Claude context**：上傳走 Replicate 的 URL 上傳 API，
  不要把參考圖 base64 塞進 LLM prompt（參考 token-saver skill）
- **每張圖都要留 metadata**：方便 paopao 回溯「這張好看的是怎麼生的」
- **技術選型不確定時問 paopao**：例如要不要換成 fal.ai、要不要加水印
