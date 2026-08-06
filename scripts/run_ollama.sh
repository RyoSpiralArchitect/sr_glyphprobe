#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-qwen3:4b}"
BASE_URL="${BASE_URL:-http://127.0.0.1:11434/v1}"
CONFIG="${CONFIG:-configs/v1_remote_surface.yaml}"

exec glyphprobe run -c "$CONFIG" \
  --backend ollama \
  --model "$MODEL" \
  --base-url "$BASE_URL" \
  "$@"
