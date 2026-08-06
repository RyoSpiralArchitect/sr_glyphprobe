#!/usr/bin/env bash
set -euo pipefail

GLYPHS="${GLYPHS:-🟤,🟫,🗿,🔄,💠,🧿,⚫,⬛,🔸,🔹}"
CONFIG="${CONFIG:-configs/v1_standard.yaml}"

exec glyphprobe run -c "$CONFIG" --emojis "$GLYPHS" "$@"
