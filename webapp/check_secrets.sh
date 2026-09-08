#!/bin/sh
# Refuse to let an API key reach git history.
#
# Run by hand before a commit:      ./check_secrets.sh
# Or install it as a git hook:      ln -sf ../../webapp/check_secrets.sh .git/hooks/pre-commit
#
# Exits non-zero if anything that looks like a real key is staged (or, when
# nothing is staged, present in the working tree).
set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0")"

# Real credentials are long; the placeholders in .env.example are not.
#   sk-ant-...  Anthropic API key      AIza...  Google / Gemini API key
#   ya29....    Google OAuth token     AQ....   Google OAuth code / token
PATTERN='sk-ant-[A-Za-z0-9_-]\{20,\}\|AIza[A-Za-z0-9_-]\{30,\}\|ya29\.[A-Za-z0-9_-]\{20,\}\|AQ\.[A-Za-z0-9_-]\{30,\}'

if git rev-parse --git-dir >/dev/null 2>&1 && ! git diff --cached --quiet 2>/dev/null; then
  SCOPE="staged changes"
  HITS=$(git diff --cached -U0 | grep -n "^+.*$PATTERN" || true)
else
  SCOPE="working tree"
  # .env is gitignored, so a key there is fine and must not block a commit.
  # .env.example IS committed, so it is deliberately still scanned.
  HITS=$(grep -rn "$PATTERN" . \
          --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ \
          --exclude=check_secrets.sh --exclude=.env 2>/dev/null || true)
fi

if [ -n "$HITS" ]; then
  echo "BLOCKED: something that looks like a real API key is in your $SCOPE:" >&2
  echo "$HITS" >&2
  echo "" >&2
  echo "Move the key into .env (gitignored) and remove it from the file above." >&2
  exit 1
fi

# Second check: .env must never be tracked.
if git rev-parse --git-dir >/dev/null 2>&1; then
  if git ls-files --error-unmatch webapp/.env .env >/dev/null 2>&1; then
    echo "BLOCKED: a .env file is tracked by git. Run:  git rm --cached .env" >&2
    exit 1
  fi
fi

echo "No API keys found in $SCOPE. Safe to commit."
