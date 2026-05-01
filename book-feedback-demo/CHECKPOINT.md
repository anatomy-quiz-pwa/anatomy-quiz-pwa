# 📍 CHECKPOINT — 《骨頭》Book Feedback 系統

**日期**：2026-05-01｜**狀態**：v1 已測試完成，v2 待寫｜**累積成本**：~$8 USD Anthropic credits

---

## 🎯 這個系統是什麼

把 MiroFish（CAMEL-AI OASIS 多 agent 模擬器）改造成「**虛擬讀者反應模擬器**」— 你貼一段 500-2000 字試寫，**25 個虛構讀者**（6 中 + 8 英 + 4 日 + 4 編輯 + 3 書評/Podcast）並行讀完並給結構化反應，聚合成 8 段 Result Card 幫你迭代修書。

底層 stack：Flask + Vue + Anthropic Claude Opus 4.7 (`claude-opus-4-7`)。

---

## 📦 已完成的東西

### 1. 後端系統（在沙箱 `/root/Projects/MiroFish/`）

新增 8 個檔（不動 MiroFish 原本的 graph/simulation/report）：

| 檔 | 用途 |
|---|---|
| `backend/app/utils/claude_client.py` | Anthropic SDK wrapper（與既有 OpenAI client 共存） |
| `backend/app/services/prompts/cohort_spec.py` | 18 reader cohort + 7 手寫 mock 編輯/書評 |
| `backend/app/services/prompts/book_feedback_prompts.py` | 4 套 prompt 集中管理（persona/reaction/card/diff） |
| `backend/app/models/feedback_session.py` | Session + 版本 + reactions 持久化（file-based） |
| `backend/app/services/book_persona_generator.py` | 並行生 18 個讀者 persona + 合併 7 mock |
| `backend/app/services/reader_reaction_engine.py` | 25 persona 並行讀同段試寫 |
| `backend/app/services/result_card_aggregator.py` | 8 段 card + Python 硬規則警報 + markdown 渲染 |
| `backend/app/services/version_diff_aggregator.py` | v_n vs v_(n+1) 反應差異聚合 |
| `backend/app/api/feedback.py` | 7 個 REST endpoint（含 `/api/feedback/ui` 內建 UI） |

### 2. v1 測試結果（《骨頭》第 3 章 跪坐）

- **session_id**：`fbs_ba661c3ab109`
- **試寫段落**：646 字（京都跪坐老太太 → 股骨頸 → 西方椅子）
- **25/25 reactions 全到齊**
- **Result Card**：8 段完整，含 6 必改、2 結構性問題、4 寫得好、2 策略決定、4 編輯立場、3 書評 voice、3 市場訊息
- **資料位置**：`/root/Projects/MiroFish/backend/uploads/feedback_sessions/fbs_ba661c3ab109/`
  - `session.json` / `personas.json` / `versions/v1.txt` / `reactions/v1.json` / `result_cards/v1.{json,md}`

### 3. 部署的前端（Vercel 靜態 demo）

- **URL（23h 免登入）**：https://anatomy-quiz-hm2329yka-anatomy-quiz-pwas-projects.vercel.app/book-feedback-demo/?_vercel_share=rErj157BBDac1uKCER13UvEJxNRSRI5A
- **GitHub**：`anatomy-quiz-pwa/anatomy-quiz-pwa` repo, branch `book-feedback-demo`, folder `book-feedback-demo/`
- **UI 特色**：兩欄式卡片 + 試寫段落 highlight 踩雷句 + checkbox 進度（localStorage）+ Notion 連結
- **永久免登入**：去 Vercel dashboard promote 最新部署到 production（`dpl_ALfGZRjFe47c4XTyfybWTtP3LPMz`）

---

## 🔴 v1 模擬抓出的 6 個必改

| # | 類型 | 問題單句／處 |
|---|---|---|
| 1 | 💣 致命單句 | 「痛是身為日本女人的一部分，像四季更迭」— **25/25 全員點名** |
| 2 | 📚 事實錯誤 | 「長達千年的協商」→ 跪坐定型於江戶以後 |
| 3 | 📚 事實錯誤 | 髕股壓力 → 股骨頸應力骨折（不同關節，不同機轉） |
| 4 | ⚠️ 缺限定語 | 「七十歲以上日本女性，幾乎人手一個髖部問題」(selection bias) |
| 5 | 🌏 文化地雷 | 「西方人發明了椅子」(中國商周早有椅子，East/West 二分過時) |
| 6 | 💣 致命單句 | 「如果我五十年前就介入，這個應力性骨折就不會發生」(PT 救世主姿態) |

## 🟢 v1 已寫得好的（不要動）

1. 開場「鶴」+ X 光片反差（13 人讚）
2. 台灣歐巴桑摔機車那一段（10+ 人笑出聲）
3. 「我必須承認...心裡有兩種聲音」段落（14 人說「不是自戀是誠實」）
4. 第四段「西方人也付出代價」雙向算帳（救了整篇）

## 🎯 你還沒決定的 2 件事（影響 v2 走向）

- [ ] **A. 老太太要不要「開口」？** 給她名字、台詞、場景 vs 保留她作為畫面。20+ persona 傾向開口，少數中文大眾讀者覺得可保留。**倫理選擇，編輯不能替你決定。**
- [ ] **B. 科普嚴謹度走哪一路？** Gawande/Lieberman 路線（補引用） vs Bryson 路線（敘事為王）。英文+日本市場要 A，中文大眾讀者要 B。**選一邊，不能兩邊都站。**

---

## 📋 編輯結論

- ❌ **田中智子（講談社）拒絕** — 「千年」事實錯誤 + essentialism，需日本本土監修
- ⚠️ **陳冠廷（大塊）/ Margaret（Penguin）/ David（Norton）皆要求修改後再評估**

## 📣 書評會公開說什麼

- **林書婷（Openbook）**：👎 不推 — 「一個台灣男性 PT 憑什麼替日本女人定義她們和痛的關係」
- **Helen Sato（Atlantic）**：📝 批判性書評 — 會公開引用「四季更迭」當 Memoirs of a Geisha framing 範例
- **中村龍也（BookCafe Tokyo）**：📝 Podcast 開頭吐槽，但會肯定第四段救了整篇

---

## ⏭️ Next Steps（你下次回來）

1. **決定 2 個策略題**（A 老太太開口 / B 科普嚴謹度）
2. **寫 v2 試寫段落**（500-2000 字，把 6 個必改 + 結構性問題納入）
3. **跑 v2 模擬**：
   - 啟動 backend：`cd /root/Projects/MiroFish && npm run backend`
   - `curl -X POST http://localhost:5001/api/feedback/session/fbs_ba661c3ab109/version -H "Content-Type: application/json" -d '{"passage": "...", "version_focus": "..."}'`
   - 等 ~3 分鐘
4. **拿 v1 vs v2 diff card**：`curl http://localhost:5001/api/feedback/session/fbs_ba661c3ab109/diff?from=v1&to=v2`
5. **重新 bake demo + 部署**：用同樣流程 push 到 `book-feedback-demo` 分支

預估 v2 跑一輪 reactions + result card + diff = ~$2-3 USD。

---

## 🔧 Resume 環境的速查

| 項目 | 路徑/指令 |
|---|---|
| Backend code | `/root/Projects/MiroFish/backend/app/` |
| Session 資料 | `/root/Projects/MiroFish/backend/uploads/feedback_sessions/fbs_ba661c3ab109/` |
| Anthropic key | 已存在 `.env` 的 `ANTHROPIC_API_KEY` |
| 啟動 backend | `cd /root/Projects/MiroFish && npm run backend` |
| Backend health | `curl http://localhost:5001/health` |
| Demo URL | https://anatomy-quiz-hm2329yka-anatomy-quiz-pwas-projects.vercel.app/book-feedback-demo/ |
| 改 prompt | 編輯 `services/prompts/book_feedback_prompts.py`（4 套 prompt 集中在這） |
| 改 persona spec | 編輯 `services/prompts/cohort_spec.py`（18 讀者 + 7 編輯/書評） |

## 📂 Notion 章節結構

CSV 章節清單 + Ch3 詳細頁 markdown 已在對話中提供，可貼到 Notion `book` 頁面。Notion URL：https://www.notion.so/book-353405855dab803c89f5eea43c82093b

---

_由 Book Feedback 模擬器 session 產生，記錄完整 v1 測試結果與 v2 工作清單_
