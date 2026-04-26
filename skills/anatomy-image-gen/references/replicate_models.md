# Replicate 模型選用紀錄

這份文件是**人類可讀的選用理由**。真正被程式讀到的是 `scripts/replicate_models.py`
裡的 `MODEL_SLUGS` 常數。兩邊要保持一致——編輯時請同時更新。

-----

## 目前預設（2026-04-26 更新）

| 模式 | Replicate 模型 | 為何選它 |
|------|----------------|----------|
| `skeleton` | `black-forest-labs/flux-schnell` | Flux schnell 是目前 Replicate 最便宜（~$0.003/張）且最穩定還在維護的 text-to-image 模型。簡化線條/骨架可以靠 prompt 控制。**目前無 ControlNet 姿勢控制**。 |
| `muscle` | `black-forest-labs/flux-schnell` | 同上。教材插圖風格透過 prompt 加 `medical illustration` 等關鍵字達成。 |
| `realistic` | `black-forest-labs/flux-dev` | Flux dev 在寫實人體比 schnell 強，貴一點但值得（~$0.025/張）。 |

### 2026-04-26 變更紀錄

`stability-ai/sdxl` 與 `jagilley/controlnet-pose` 已從 Replicate 預設可呼叫名單下架（`replicate.run()` 回 404）。先切到 Flux 系列確保 pipeline 跑得起來。**代價：失去從參考照抓姿勢的 ControlNet 功能**——目前所有模式都是純 text-to-image。

下次優先補：找一個 2026 仍在維護的 ControlNet OpenPose 模型，把姿勢控制加回來。候選查找路徑：
- https://replicate.com/explore → ControlNet 標籤
- 看 stars / 最近 push 時間
- 確認 input schema 有 `image` 欄位

-----

## 挑選標準（未來更換時對照用）

⚠️ Replicate 上新模型很快，動工前（尤其 Phase 2 之後）先去 https://replicate.com/explore
確認有沒有更好的候選。評估條件：

1. **支援 ControlNet OpenPose**（姿勢控制是核心需求）
2. **2025 年後仍在維護**（看最近 push 時間）
3. **每秒成本 < $0.005 USD**（批次 30–50 張要划算）
4. **有官方文件和 input schema**（避免踩坑）
5. **輸出解析度 ≥ 1024x1024**（投影片夠用）

-----

## 版本釘選策略

目前用「不釘版本」的 slug（例如 `stability-ai/sdxl`），這會用最新 default version。

**好處**：paopao 不用手動升級
**壞處**：模型更新可能導致風格飄移

若要穩定化某堂課的全部圖，可在 `replicate_models.py` 改為釘版本：

```python
MODEL_SLUGS = {
    "muscle": "stability-ai/sdxl:7762fd07...",
    ...
}
```

版本 hash 可在 Replicate 的 model 頁面 → Versions 找到。

-----

## 候選替代模型（未來評估用）

- `lucataco/sdxl-controlnet` — SDXL + 已打包好的多種 ControlNet，API 更省事
- `fofr/realvisxl-v3-multi-controlnet-lora` — 寫實人體更穩，可能取代 flux-dev
- `cjwbw/anything-v3-better-vae` — 若 paopao 未來想要動漫風教材（目前不需要）

選用前先在 Replicate Playground 跑 1–2 張看風格。

-----

## 修改步驟

1. 改 `scripts/replicate_models.py` 的 `MODEL_SLUGS`
2. 同步更新本文件第一個表格
3. 跑一張測試圖確認風格沒跑掉
4. 寫到 `references/examples.md` 當成新基準
