# 成功範例對照表

當 Phase 2 跑通第一批測試圖後，把「prompt + 結果圖截圖 + 選用理由」記在這裡。
未來 paopao 或 Claude Code 要重現某個風格時，可以直接參考。

> 目前是 Phase 1（尚未實際呼叫 Replicate），以下是預期範例結構。
> 實際結果圖產出後，把路徑補到 `result_image` 欄位。

-----

## 範例 1：跑步擺盪期 — 髖屈肌群（muscle）

- **paopao 原始描述**：`側面視角，顯示髖屈肌群，跑步擺盪期`
- **Mode**：`muscle`
- **Model**：`stability-ai/sdxl`
- **Resolved positive prompt**：
  ```
  side view, running swing phase with hip flexor muscles highlighted,
  medical illustration of muscle anatomy, labeled muscle groups,
  anatomical accuracy, semi-transparent skin showing deep muscles,
  textbook quality color illustration,
  clean educational illustration style, professional anatomy textbook quality,
  clear lines, high contrast, neutral background, accurate human proportions
  ```
- **Negative prompt**：（見 `prompt_builder.MODE_NEGATIVE["muscle"]`）
- **Seed**：TBD
- **Result image**：TBD（Phase 2 補）
- **Paopao 評語**：TBD

-----

## 範例 2：深蹲最低點 — 骨架分析（skeleton）

- **paopao 原始描述**：`深蹲最低點側面骨架，顯示膝蓋與髖關節角度`
- **Mode**：`skeleton`
- **Model**：`jagilley/controlnet-pose`
- **Result image**：TBD

-----

## 範例 3：硬舉起始位 — 真人示範（realistic）

- **paopao 原始描述**：`硬舉起始位側面，中性脊椎`
- **Mode**：`realistic`
- **Model**：`black-forest-labs/flux-dev`
- **Result image**：TBD

-----

## 回溯某張好看圖的流程

每張實際產出的圖旁都有一個 `.json` metadata。打開那個 JSON：

```json
{
  "prompt": "...",
  "negative_prompt": "...",
  "model": "stability-ai/sdxl",
  "seed": 42,
  ...
}
```

複製 `prompt` / `negative_prompt` / `seed` / `model`，就能在 Replicate Playground
或本 skill 重現同一張。
