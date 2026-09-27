#!/usr/bin/env bash
# One-time setup of text-factor-space on macOS. Run it (do not `source` it) from anywhere, e.g. in
# Cursor's terminal:   bash scripts/bootstrap_mac.sh
#
# What it does, in order (safe to re-run; every step checks before acting):
#   1. checks git, Python >= 3.10 and the GitHub CLI (gh)
#   2. checks that GitHub access already works; it NEVER asks for a password or token
#   3. makes this folder a git repo on branch main with one initial commit (only if it has no commits)
#   4. creates github.com/akraghavan/text-factor-space (public) if missing, sets `origin`, pushes main
#   5. creates .venv and installs the core requirements (no torch)
#   6. runs the tests (unimplemented tfs_stats functions show as SKIPPED)
#   7. starts Claude Code here (set TFS_NO_CLAUDE=1 to skip)
# It never force-pushes, never commits data/ or data files, and aborts if a data file is tracked.

# Refuse to be sourced: `exit` would close your terminal.
if [ -n "${ZSH_EVAL_CONTEXT:-}" ]; then
  case "$ZSH_EVAL_CONTEXT" in *:file*) echo "Run it, don't source it:  bash scripts/bootstrap_mac.sh"; return 1 ;; esac
fi
# Started from zsh/sh (e.g. `zsh scripts/bootstrap_mac.sh`)? Re-run under bash.
if [ -z "${BASH_VERSION:-}" ]; then exec bash "$0" "$@"; fi
if [ "${BASH_SOURCE[0]}" != "$0" ]; then echo "Run it, don't source it:  bash scripts/bootstrap_mac.sh"; return 1; fi

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_DIR"

REPO_SLUG="${TFS_REPO:-akraghavan/text-factor-space}"
REPO_OWNER="${REPO_SLUG%%/*}"
REPO_DESC="Do 10-K business descriptions define economic neighbours that explain, model and predict US stock returns? Code and docs only; CRSP/Compustat data are not included."
CLAUDE_MODEL="claude-opus-5-5"
CLAUDE_EFFORT="high"

# Never let git or gh stop to ask for credentials; fail fast with a message instead.
export GIT_TERMINAL_PROMPT=0
export GH_PROMPT_DISABLED=1
export GCM_INTERACTIVE=never

# Homebrew's bin dirs, in case this terminal's PATH lacks them (appended, so nothing is shadowed).
for d in /opt/homebrew/bin /usr/local/bin; do
  case ":$PATH:" in *":$d:"*) ;; *) if [ -d "$d" ]; then PATH="$PATH:$d"; fi ;; esac
done
export PATH

# ---------------------------------------------------------------------------------------------------
if [ -t 1 ]; then B=$'\033[1m'; R=$'\033[1;31m'; G=$'\033[32m'; Z=$'\033[0m'; else B=""; R=""; G=""; Z=""; fi
STEP=0; NSTEPS=7
step() { STEP=$((STEP + 1)); printf '\n%s==> [%d/%d] %s%s\n' "$B" "$STEP" "$NSTEPS" "$*" "$Z"; }
ok()   { printf '    %sok%s  %s\n' "$G" "$Z" "$*"; }
note() { printf '    %s\n' "$*"; }
die()  {
  printf '\n%sSTOPPED:%s %s\n' "$R" "$Z" "$1" >&2; shift
  for line in "$@"; do printf '    %s\n' "$line" >&2; done
  printf '\n    Then re-run:  bash scripts/bootstrap_mac.sh   (safe to re-run)\n' >&2
  exit 1
}
py_ok() { "$1" -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; }

# Public repo: nothing licensed or secret may be pushed. Checks the index AND every commit on HEAD.
DATA_RE='^data/|\.(parquet|csv|csv\.gz|zip|npz|npy|pkl)$'
assert_publishable() {
  local bad
  bad="$(git ls-files | grep -E "$DATA_RE" | grep -vx 'data/README.md' || true)"
  if [ -n "$bad" ]; then
    die "These data files are tracked by git and must never reach the public repo:" \
        "$(printf '%s\n' "$bad" | head -n 20 | sed 's/^/    /')" \
        "Untrack them (the files stay on disk):  git rm -r --cached <path>   then commit"
  fi
  bad="$({ git log --format= --name-only HEAD 2>/dev/null || true; } | grep -E "$DATA_RE" | grep -vx 'data/README.md' | sort -u || true)"
  if [ -n "$bad" ]; then
    die "These data files are in this branch's git HISTORY; pushing would publish them:" \
        "$(printf '%s\n' "$bad" | head -n 20 | sed 's/^/    /')" \
        "Nothing was pushed. The history has to be rewritten before the first push;" \
        "ask Claude Code to do it (do not push until it is done)."
  fi
  if git grep --cached -qIE '(ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' 2>/dev/null; then
    die "A token or private key appears in a tracked file:" \
        "$(git grep --cached -lIE '(ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' | tr '\n' ' ')" \
        "Remove it and untrack the file before pushing."
  fi
}
origin_url() { git config --get remote.origin.url 2>/dev/null || true; }  # raw URL, before insteadOf rewrites
origin_is_repo() { printf '%s\n' "$(origin_url)" | grep -Eq "github\.com[:/]${REPO_SLUG}(\.git)?/?\$"; }
set_origin() {  # $1 = URL
  if git remote get-url origin >/dev/null 2>&1; then
    note "origin was $(origin_url); pointing it at $1"
    git remote set-url origin "$1"
  else
    git remote add origin "$1"
  fi
}
push_main() {  # $1 = how we authenticate (for the message)
  assert_publishable
  if git push -u origin main; then
    ok "pushed main to github.com/$REPO_SLUG ($1)"
  else
    die "git push failed. Nothing was force-pushed." \
        "If GitHub has commits this folder lacks:  git pull --rebase origin main" \
        "If it says authentication/permission denied:  gh auth status   (must be logged in as $REPO_OWNER)"
  fi
}

printf '%stext-factor-space bootstrap%s   (repo folder: %s)\n' "$B" "$Z" "$REPO_DIR"
[ -f requirements.txt ] && [ -f .gitignore ] && [ -d tfs_stats ] \
  || die "This does not look like the text-factor-space folder (missing requirements.txt, .gitignore or tfs_stats/)."

# ---------------------------------------------------------------------------------------------------
step "Prerequisites"
command -v git >/dev/null 2>&1 \
  || die "git is not installed." "Install it:  xcode-select --install     (or: brew install git)"
ok "$(git --version)"

PY=""
for c in ${TFS_PYTHON:-} python3.11 python3.12 python3.13 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && py_ok "$c"; then PY="$(command -v "$c")"; break; fi
done
[ -n "$PY" ] || die "No Python >= 3.10 found (the python3 that ships with macOS is 3.9)." \
  "Install one:  brew install python@3.11      (Homebrew itself: https://brew.sh)"
ok "Python $("$PY" -c 'import platform; print(platform.python_version())') at $PY"

HAVE_GH=0
if command -v gh >/dev/null 2>&1; then ok "$(gh --version | head -n 1)"; HAVE_GH=1
else note "GitHub CLI (gh) not found; will try your existing git credentials instead."; fi

# ---------------------------------------------------------------------------------------------------
step "GitHub access (no credential prompts)"
GH_USER=""
if [ "$HAVE_GH" = 1 ]; then
  if gh auth status --hostname github.com >/dev/null 2>&1 || gh api user --jq .login >/dev/null 2>&1; then
    GH_USER="$(gh api user --jq .login 2>/dev/null || true)"
    ok "gh is logged in to github.com as ${GH_USER:-<unknown>}"
    if [ -n "$GH_USER" ] && [ "$GH_USER" != "$REPO_OWNER" ]; then
      die "gh is logged in as '$GH_USER', but the repo belongs to '$REPO_OWNER'." \
          "If both accounts are logged in:  gh auth switch --user $REPO_OWNER" \
          "Otherwise log in as $REPO_OWNER:  gh auth login"
    fi
    gh auth setup-git --hostname github.com
    ok "git will use gh's credentials for github.com (gh auth setup-git)"
  else
    HAVE_GH=0
    note "gh is installed but not logged in; will try your existing git credentials instead."
  fi
fi

# ---------------------------------------------------------------------------------------------------
step "Local git repository"
if [ "$(git rev-parse --show-toplevel 2>/dev/null || true)" != "$REPO_DIR" ]; then
  git init -q .
  git symbolic-ref HEAD refs/heads/main
  ok "initialised a new git repo on branch main"
else
  ok "already a git repo"
fi

HAS_COMMITS=0
if git rev-parse -q --verify HEAD >/dev/null; then HAS_COMMITS=1; fi
BRANCH="$(git symbolic-ref --short -q HEAD || true)"
if [ "$BRANCH" != "main" ]; then
  if [ "$HAS_COMMITS" = 0 ]; then
    git symbolic-ref HEAD refs/heads/main
  elif [ "$BRANCH" = "master" ] && ! git show-ref -q --verify refs/heads/main; then
    git branch -m master main; ok "renamed branch master -> main"
  else
    die "You are on '${BRANCH:-a detached HEAD}', but this script pushes 'main'." "Switch first:  git switch main"
  fi
fi

if [ -z "$(git config user.email || true)" ]; then
  if [ "$HAVE_GH" = 1 ]; then
    GH_ID="$(gh api user --jq .id)"; GH_NAME="$(gh api user --jq '.name // .login')"
    git config user.name "$GH_NAME"
    git config user.email "${GH_ID}+${GH_USER}@users.noreply.github.com"
    ok "git identity for this repo only: $GH_NAME <${GH_ID}+${GH_USER}@users.noreply.github.com> (keeps your email private)"
  else
    die "git has no author identity configured (needed for the first commit)." \
        "Either log in the GitHub CLI once (brew install gh && gh auth login) and this script" \
        "sets a private noreply identity for this repo, or set one yourself:" \
        "  git config --global user.name \"Abhinav Raghavan\"" \
        "  git config --global user.email \"<your GitHub noreply address or email>\""
  fi
fi

if [ "$HAS_COMMITS" = 0 ]; then
  git add -A
  assert_publishable
  git commit -q -m "Initial commit: text-factor-space scaffold" \
    -m "Code and docs only; data/ is gitignored (CRSP/Compustat are licensed and not redistributed)." \
    -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01RmzHHcXZgHJw8QQFom79S8"
  ok "initial commit $(git rev-parse --short HEAD) ($(git ls-files | wc -l | tr -d ' ') files; data excluded)"
else
  ok "existing history: $(git rev-list --count HEAD) commit(s); nothing new committed by this script"
  if [ -n "$(git status --porcelain)" ]; then
    note "Uncommitted changes exist; they are not pushed (commit them from Claude Code)."
  fi
fi

# ---------------------------------------------------------------------------------------------------
step "GitHub repository github.com/$REPO_SLUG"
assert_publishable
if [ "$HAVE_GH" = 1 ]; then
  if [ "$(gh config get git_protocol -h github.com 2>/dev/null || true)" = "ssh" ]; then
    WANT_URL="git@github.com:${REPO_SLUG}.git"
  else
    WANT_URL="https://github.com/${REPO_SLUG}.git"
  fi
  if VIEW_ERR="$(gh repo view "$REPO_SLUG" --json name 2>&1 >/dev/null)"; then
    ok "github.com/$REPO_SLUG exists"
    origin_is_repo || set_origin "$WANT_URL"
    ok "origin -> $(origin_url)"
    push_main "gh credentials"
  elif printf '%s\n' "$VIEW_ERR" | grep -q "Could not resolve to a Repository"; then
    if git remote get-url origin >/dev/null 2>&1; then
      gh repo create "$REPO_SLUG" --public --description "$REPO_DESC"
      set_origin "$WANT_URL"
      push_main "gh credentials"
    else
      gh repo create "$REPO_SLUG" --public --description "$REPO_DESC" --source=. --remote=origin --push
      ok "created github.com/$REPO_SLUG (public) and pushed main"
    fi
  else
    die "Could not reach GitHub through gh:" "$VIEW_ERR" "Check your network, then re-run."
  fi
else
  # No usable gh login: fall back to whatever git credentials this Mac already has (keychain, SSH key).
  HTTPS_URL="https://github.com/${REPO_SLUG}.git"
  if origin_is_repo || git ls-remote "$HTTPS_URL" >/dev/null 2>&1; then
    origin_is_repo || set_origin "$HTTPS_URL"
    ok "github.com/$REPO_SLUG exists; origin -> $(origin_url)"
    if git push -u origin main; then
      ok "pushed main using your existing git credentials"
    else
      die "ACTION NEEDED (the only manual step): git has no saved GitHub login this script can use." \
          "One-time GitHub CLI login:  brew install gh && gh auth login" \
          "   (choose GitHub.com -> HTTPS -> Login with a web browser; log in as $REPO_OWNER)"
    fi
  else
    die "ACTION NEEDED (the only manual step): github.com/$REPO_SLUG does not exist yet, and creating it needs the GitHub CLI." \
        "One-time GitHub CLI login:  brew install gh && gh auth login" \
        "   (choose GitHub.com -> HTTPS -> Login with a web browser; log in as $REPO_OWNER)" \
        "Alternative without gh: create an EMPTY public repo named text-factor-space at https://github.com/new" \
        "   (no README, licence or .gitignore), then re-run; your existing git login is used for the push."
  fi
fi

# ---------------------------------------------------------------------------------------------------
step "Python environment (.venv, core requirements, no torch)"
if py_ok .venv/bin/python; then
  ok "reusing .venv ($(.venv/bin/python -c 'import platform; print(platform.python_version())'))"
else
  if [ -e .venv ]; then note "existing .venv is unusable or older than Python 3.10; rebuilding it"; fi
  "$PY" -m venv --clear .venv
  ok "created .venv with $PY"
fi
note "installing requirements.txt (first run takes a few minutes)..."
.venv/bin/python -m pip install --quiet --disable-pip-version-check --upgrade pip
.venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt
ok "core requirements installed (embedding stage needs: pip install -r requirements-nlp.txt)"

# ---------------------------------------------------------------------------------------------------
step "Tests"
if .venv/bin/python -m pytest -q; then
  ok "test suite ran clean (skipped = tfs_stats functions not written yet)"
else
  note "Some tests FAILED (see above). Setup is otherwise complete; continuing."
fi

# ---------------------------------------------------------------------------------------------------
step "Claude Code"
printf '\n%sSetup complete.%s Repo: https://github.com/%s\n' "$B" "$Z" "$REPO_SLUG"
note "To start Claude Code in this folder later:"
note "  cd \"$REPO_DIR\" && source .venv/bin/activate && claude --model $CLAUDE_MODEL --effort $CLAUDE_EFFORT"
if [ -n "${TFS_NO_CLAUDE:-}" ]; then
  note "TFS_NO_CLAUDE is set; not starting Claude Code."
elif command -v claude >/dev/null 2>&1; then
  export VIRTUAL_ENV="$REPO_DIR/.venv"
  export PATH="$REPO_DIR/.venv/bin:$PATH"
  note "Starting it now. If it asks you to log in, that is Claude's own login, not GitHub."
  exec claude --model "$CLAUDE_MODEL" --effort "$CLAUDE_EFFORT"
else
  note "The 'claude' command is not on PATH. Install Claude Code:  npm install -g @anthropic-ai/claude-code"
fi
