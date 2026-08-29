#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 6 ]]; then
  echo "usage: $0 RUN_ROOT PREFLIGHT_DIR T11_PREFLIGHT_DIR LOG_DIR LLAMA32_MODEL_PATH SMOLLM2_MODEL_PATH" >&2
  exit 64
fi

run_root=$1
preflight_dir=$2
t11_preflight_dir=$3
log_dir=$4
llama32_model_path=$5
smollm2_model_path=$6
mkdir -p "$run_root" "$log_dir"

roles=(
  qwen25_0p5b_base_bf16
  llama32_3b_base_bf16
  qwen25_7b_base_bf16
  olmo2_1b_base_bf16
  qwen25_1p5b_base_bf16
  smollm2_1p7b_base_bf16
  gemma2_2b_it_bf16
  qwen25_3b_base_bf16
  mistral7b_instruct_v03_bf16
)

for role in "${roles[@]}"; do
  model_args=()
  if [[ "$role" == "llama32_3b_base_bf16" ]]; then
    model_args=(--model-path "$llama32_model_path")
  elif [[ "$role" == "smollm2_1p7b_base_bf16" ]]; then
    model_args=(--model-path "$smollm2_model_path")
  fi
  python scripts/emoji_steering_specificity_harvest_v0.py run-role \
    --role "$role" \
    --run-root "$run_root" \
    --preflight-dir "$preflight_dir" \
    --t11-preflight-dir "$t11_preflight_dir" \
    "${model_args[@]}" \
    >>"$log_dir/$role.log" 2>&1
done
