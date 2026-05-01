# Anatomy Image Gen — Checkpoint

> 最後更新：2026-04-26
> 給未來的 paopao（或下一個接手的 Claude）看的進度檔。
> 看完這份就知道現在卡在哪、下次要做什麼。

-----

## 一句話現況

**Phase 2 中段**：付費、token、API 都通了；圖會生出來，**但品質還不能用在課程上**。
正在摸索「Flux 真的擅長什麼類型的圖」。

-----

## ✅ 已完成

| 項目 | 狀態 |
|------|------|
| Skill 程式碼結構（`skills/anatomy-image-gen/`） | 都在 git，跑得起來 |
| `SKILL.md` 觸發關鍵字、流程說明 | OK |
| `prompt_builder.py` 中文→英文 prompt | 離線測過 OK |
| `replicate_client.py` token / retry / 錯誤分類 | 跑過 402、404 都正確處理 |
| `generate.py` 單張 CLI | 可跑 |
| `batch_generate.py` 批次 CLI | 跑過 dry-run 沒測過實機 |
| Replicate token 設定 | 已寫進 `~/.zshrc`（⚠️ 見下方安全警告）|
| Replicate billing | 已加卡、儲 $10 USD |
| 第一張實機生成 | 跑出來了，**但品質不能用** |

-----

## 🔴 已知問題

### 問題 1：Replicate 上的 ControlNet 模型已下架

- 原本 spec 計畫用 `jagilley/controlnet-pose` + `stability-ai/sdxl` + ControlNet
- 2026-04-26 實測：兩個都 404
- **後果**：失去「從照片抓姿勢」的核心功能
- 目前 fallback 到 `black-forest-labs/flux-schnell` 和 `flux-dev`，但這些是**純 text-to-image**（不看你的參考照）

### 問題 2：Flux 的解剖醫學精準度不夠

- 第一張試生「跑步擺盪期髖屈肌群」→ 出來一個站著的人，肌肉位置亂、標籤是亂碼
- AI 圖像模型本來就不懂醫學，且**畫不好任何文字**（中文尤其）
- **結論**：當「真正的教學圖」用不了，當「概念示意 / 投影片背景」可以

### 問題 3：Token 安全性（待處理）

- ⚠️ paopao 在對話過程中曾把 token 貼出來
- 雖然提醒過要撤銷重建，但實際使用的 token 開頭仍是 `r8_WG`，與洩漏的那個前綴一致
- **未確認是否已輪替**。建議下次回來第一件事：檢查 `https://replicate.com/account/api-tokens` 撤銷舊 token、建新 token、寫入 `~/.zshrc`、設 spending limit

-----

## 💰 花費紀錄

| 日期 | 項目 | 金額 |
|------|------|------|
| 2026-04-26 | Replicate 儲值 | $10.00 USD |
| 2026-04-26 | 1 張 flux-schnell 測試 | ~$0.003 USD |

**剩餘餘額**：~$9.99 USD（Replicate 預付不過期）

-----

## 🎯 開放問題（paopao 要決定）

### Q1：要不要繼續找 ControlNet？

- 如果你**必須要「照學員姿勢生圖」**這個功能 → 必須繼續挖（A 路線）
- 如果你**只要「漂亮的解剖示意圖當素材」** → Flux 就夠（B 路線）

### Q2：要用 $10 跑哪幾類圖？

目前傾向 **B 路線**——用 Flux 跑可以實際用上的素材。
還沒決定具體要跑什麼。候選：
- 課程主視覺 / 章節封面
- 投影片背景圖
- IG / FB 社群封面
- icon / 設計元素

### Q3：是否該保留這個工具？

- 單張生圖：直接用 Nano Banana / ChatGPT 比這個工具好
- **這個工具的真正價值**：批次（一次跑 20-50 張同風格）+ 可重現（每張有 metadata）
- 如果未來不會做批次需求 → 工具可以收

-----

## 🔜 下次回來，照這順序做

### 1.（5 分鐘）安全：輪替 token + 設花費上限

```bash
# 1. 開 https://replicate.com/account/api-tokens 撤銷現有 token、建新的
# 2. 開 https://replicate.com/account/billing → Spending limits → 設月上限 $20
# 3. 在 Mac Terminal：
sed -i.bak '/REPLICATE_API_TOKEN/d' ~/.zshrc
echo 'export REPLICATE_API_TOKEN=新的token' >> ~/.zshrc
source ~/.zshrc
```

### 2.（要決定）回答 Q1 與 Q2

跟 Claude 說：
- 要不要花時間挖 ControlNet（A 路線）
- 要跑什麼類型的圖（給課程情境、品牌色、優先用途）

### 3.（看決定）執行

- 走 A：Claude 去 Replicate 找 ControlNet 模型 → 換 model 註冊表 → 重測
- 走 B：寫 starter CSV → 批次跑 → 你挑能用的留

### 4. 把實際生成的好圖寫進 `references/examples.md`

每張附 prompt + seed + model，未來要重現有依據。

-----

## 📁 關鍵檔案位置

```
~/anatomy-quiz-pwa/
├── skills/anatomy-image-gen/
│   ├── SKILL.md                          # 觸發/流程說明
│   ├── CHECKPOINT.md                     # ← 你正在看的這份
│   ├── scripts/
│   │   ├── generate.py                   # 單張 CLI
│   │   ├── batch_generate.py             # 批次 CLI
│   │   ├── prompt_builder.py             # 中文→英文
│   │   ├── replicate_client.py           # API 包裝
│   │   └── replicate_models.py           # 模型註冊表（要換 model 改這裡）
│   ├── references/
│   │   ├── modes.md                      # 三種模式說明
│   │   ├── replicate_models.md           # 模型選用紀錄
│   │   └── examples.md                   # 成功範例（待補）
│   └── assets/
│       └── batch_template.csv            # 批次範本

~/Desktop/boneman/
├── refs/                                 # 參考照
│   └── PRI-1024x704.jpg                  # 第一張測試用
└── generated/                            # 產出
```

-----

## 💡 給下次接手的提醒

1. **每次開新 Terminal 要做這兩件事**：
   ```bash
   cd ~/anatomy-quiz-pwa
   source .venv/bin/activate
   ```
   看到 prompt 開頭有 `(.venv)` 才算啟動成功。

2. **生圖之前先 dry-run**：加 `--dry-run` 旗標，看 prompt 對不對再花錢。

3. **Replicate 模型很容易過期**：跑出 404 = 模型下架了，去 `replicate_models.py` 換 slug。

4. **沉沒成本不要影響決策**：如果發現工具不適合你的真實需求，**收掉沒關係**。$10 餘額不會跑掉，未來想用再用。

5. **誠實的判斷**：AI 生解剖圖目前不到「印在教材上」的品質。當投影片裝飾圖、社群封面是合理使用範圍。
