#!/usr/bin/env bash
# Codespace post-create: CLIs the agent workflow depends on.
set -euo pipefail

echo "[post-create] installing hyperframes CLI (pinned)…"
npm i -g hyperframes@0.8.38

echo "[post-create] installing heygen CLI…"
curl -fsSL https://static.heygen.ai/cli/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"

echo "[post-create] verifying…"
hyperframes --version || echo "hyperframes: check npm global path"
heygen --version || echo "heygen: install failed — see docs/KEYS.md"

cat <<'EOF'

== setup checklist for the human ==
1. Secrets auto-inject as env vars: PEXELS_API_KEY, GROQ_API_KEY
   (repo → Settings → Secrets → Codespaces). See docs/KEYS.md.
2. HeyGen (SFX/BGM catalog): inside this codespace run
       export BROWSER=none HEYGEN_NO_BROWSER=1
       heygen auth login --oauth
   then open the printed URL in YOUR browser. Free-usage OAuth path.
   (Or set a HEYGEN_API_KEY secret instead — that bills API credits.)
3. Then: npm run check && npx hyperframes preview --background

EOF
