## Hi there 👋

<!--
**anatomy-quiz-pwa/anatomy-quiz-pwa** is a ✨ _special_ ✨ repository because its `README.md` (this file) appears on your GitHub profile.

Here are some ideas to get you started:

- 🔭 I’m currently working on ...
- 🌱 I’m currently learning ...
- 👯 I’m looking to collaborate on ...
- 🤔 I’m looking for help with ...
- 💬 Ask me about ...
- 📫 How to reach me: ...
- 😄 Pronouns: ...
- ⚡ Fun fact: ...
-->

## 開發設定

### 一鍵安裝本機安全掃描(必做一次)

新人 clone 下來後,只要在專案根目錄跑這一條指令:

```bash
./setup-security.sh
```

它會自動:

1. 安裝 `pre-commit`(優先用 `pipx`,其次 `brew` 或 `pip --user`)
2. 把 git hook 註冊到 `.git/hooks/pre-commit`
3. 預先下載/快取所有掃描工具(Gitleaks、Semgrep、Bandit、Ruff)
4. 跑一次全專案 baseline 掃描
5. 產生 `.gitleaksignore` / `.semgrepignore` 範本(若不存在)

之後每次 `git commit` 都會**自動**跑掃描,不需要手動觸發。
第一次跑會比較慢(約 1–3 分鐘),之後因為有 cache,只會花幾秒。

### 三層自動化掃描架構

| 階段 | 觸發時機 | 跑什麼 | 行為 |
|------|----------|--------|------|
| 本機 commit | `git commit` | Gitleaks、Semgrep、Bandit(HIGH)、Ruff、基礎 hooks | 嚴重問題**擋住** commit |
| 雲端 push / PR | `git push`、開 PR | CodeQL、Trivy、Gitleaks history、Semgrep | 結果上傳到 **Security tab** |
| 雲端排程 | 每週一 03:17 UTC | 同上(用最新漏洞 DB) | 偵測新公布的 CVE |

### 處理常見誤報

| 工具 | 做法 |
|------|------|
| **Gitleaks** | 從 commit log 複製 `Fingerprint`,貼進 `.gitleaksignore` |
| **Semgrep** | 在該行尾加 `# nosemgrep: <rule-id>`,或把整個路徑加進 `.semgrepignore` |
| **Bandit** | 在該行尾加 `# nosec <rule-id>`(例如 `# nosec B105`) |
| **Ruff** | 在該行尾加 `# noqa: <rule-code>`(例如 `# noqa: S105`) |

緊急情況下可以用環境變數整批跳過(請只在真的卡住時使用):

```bash
SKIP=gitleaks,semgrep git commit -m "wip"
```

### 手動重跑完整掃描

```bash
# 跑所有 hooks 對全部檔案(不只是 staged 的)
pre-commit run --all-files

# 加跑 Trivy 深度漏洞掃描(預設只在手動觸發時跑)
pre-commit run trivy --hook-stage manual --all-files

# 升級所有 hook 到最新版本
pre-commit autoupdate
```

### 雲端結果在哪看

- **Code scanning alerts**:`Security` → `Code scanning`
- **Dependabot 漏洞 / PR**:`Security` → `Dependabot` 與 `Pull requests`
- **Secret scanning alerts**:`Security` → `Secret scanning`
- **Workflow logs**:`Actions` → `security`
