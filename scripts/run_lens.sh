#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-openai-community/gpt2}"
DEVICE="${DEVICE:-cuda}"
DTYPE="${DTYPE:-float32}"
CONFIG="${CONFIG:-configs/v1_standard.yaml}"

exec glyphprobe run -c "$CONFIG" \
  --backend lens \
  --model "$MODEL" \
  --device "$DEVICE" \
  --dtype "$DTYPE" \
  "$@"
