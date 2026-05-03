#!/usr/bin/env bash
# setup-security.sh — One-shot installer for local Shift-Left security tooling.
#
# What this does:
#   1. Installs pre-commit (via pipx > pip > brew, in that order of preference)
#   2. Installs the git hooks defined in .pre-commit-config.yaml
#   3. Pre-warms the tool cache so the first `git commit` is fast
#   4. Runs a baseline scan of the entire repository
#   5. Generates ignore-file templates if they do not yet exist
#
# Re-runnable any time. Safe to run after pulling new commits.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { printf "${BLUE}==>${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$*"; }
err()  { printf "${RED}✗${NC} %s\n" "$*" >&2; }

# ---------------------------------------------------------------------------
# Step 1: ensure pre-commit is installed
# ---------------------------------------------------------------------------
install_precommit() {
  if command -v pre-commit >/dev/null 2>&1; then
    ok "pre-commit already installed: $(pre-commit --version)"
    return
  fi

  log "Installing pre-commit..."
  if command -v pipx >/dev/null 2>&1; then
    pipx install pre-commit
  elif command -v brew >/dev/null 2>&1; then
    brew install pre-commit
  elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --user pre-commit
    # Ensure ~/.local/bin (pip --user target) is on PATH for this run
    export PATH="$HOME/.local/bin:$PATH"
  elif command -v pip >/dev/null 2>&1; then
    pip install --user pre-commit
    export PATH="$HOME/.local/bin:$PATH"
  else
    err "No package manager found. Install Python 3 + pip, or Homebrew, then re-run."
    exit 1
  fi

  if ! command -v pre-commit >/dev/null 2>&1; then
    err "pre-commit installation finished, but the binary is not on PATH."
    err "Add the install location (e.g. \$HOME/.local/bin) to your shell PATH and re-run."
    exit 1
  fi

  ok "pre-commit installed: $(pre-commit --version)"
}

# ---------------------------------------------------------------------------
# Step 2: register the git hook
# ---------------------------------------------------------------------------
install_hooks() {
  log "Registering git hooks (pre-commit + commit-msg)..."
  pre-commit install --install-hooks --overwrite
  ok "Hooks installed at .git/hooks/pre-commit"
}

# ---------------------------------------------------------------------------
# Step 3: generate ignore-file templates if missing
# ---------------------------------------------------------------------------
seed_ignore_files() {
  if [[ ! -f .gitleaksignore ]]; then
    log "Creating .gitleaksignore template..."
    cat > .gitleaksignore <<'EOF'
# Gitleaks ignore file.
# Each line is a fingerprint of a known false-positive secret finding.
# Format: <commit-sha>:<file>:<rule-id>:<line>
# Get the fingerprint from gitleaks output (after "Fingerprint:").
#
# Example:
#   abc1234567890:src/example.py:generic-api-key:42
EOF
    ok "Created .gitleaksignore"
  else
    ok ".gitleaksignore already exists"
  fi

  if [[ ! -f .semgrepignore ]]; then
    log "Creating .semgrepignore template..."
    cat > .semgrepignore <<'EOF'
# Semgrep path-based ignore file. Same syntax as .gitignore.
# Use this for paths to skip entirely.
# To silence a single line instead, add `# nosemgrep: rule-id` on that line.

.venv/
node_modules/
static/
templates/
*.min.js
practice_record.json
EOF
    ok "Created .semgrepignore"
  else
    ok ".semgrepignore already exists"
  fi
}

# ---------------------------------------------------------------------------
# Step 4: baseline scan
# ---------------------------------------------------------------------------
baseline_scan() {
  log "Running baseline scan (this is slow on first run, fast afterwards)..."
  if pre-commit run --all-files; then
    ok "Baseline scan clean."
  else
    warn "Baseline scan reported findings. Review the output above."
    warn "Auto-fixable issues (formatting, EOF) have already been written to disk."
    warn "Stage and commit those, then re-run this script."
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  log "Shift-Left security setup for anatomy-quiz-pwa"
  echo

  install_precommit
  install_hooks
  seed_ignore_files
  baseline_scan

  echo
  ok "Setup complete!"
  echo
  echo "Next steps:"
  echo "  1. Review any findings above and fix or whitelist them."
  echo "     - Secrets:  add fingerprint to .gitleaksignore"
  echo "     - Semgrep:  add '# nosemgrep: <rule-id>' on the offending line"
  echo "     - Bandit:   add '# nosec <rule-id>' on the offending line"
  echo
  echo "  2. From now on, every 'git commit' runs the hooks automatically."
  echo
  echo "  3. To run a deep manual scan including Trivy vulnerability DB:"
  echo "       pre-commit run --all-files"
  echo "       pre-commit run trivy --hook-stage manual --all-files"
  echo
  echo "  4. Push to GitHub — the cloud workflow at"
  echo "     .github/workflows/security.yml will run CodeQL + Trivy +"
  echo "     Gitleaks and report results in the repo's Security tab."
}

main "$@"
