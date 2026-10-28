#!/usr/bin/env bash
# Resolve one media asset into the project via media-use (HeyGen catalog path).
# Usage: ./scripts/resolve_media.sh <sfx|bgm|image|icon> "<intent text>"
set -euo pipefail

TYPE="${1:?usage: resolve_media.sh <sfx|bgm|image|icon> \"<intent text>\"}"
INTENT="${2:?usage: resolve_media.sh <sfx|bgm|image|icon> \"<intent text>\"}"

npx --yes hyperframes@latest media-use resolve --doctor \
  || echo "WARN: doctor reported problems — resolving may fail (see docs/TROUBLESHOOT.md)"

npx --yes hyperframes@latest media-use resolve \
  --type "$TYPE" \
  --intent "$INTENT" \
  --project . \
  --provider heygen

echo "done — check .media/ and the manifest for the new record."
