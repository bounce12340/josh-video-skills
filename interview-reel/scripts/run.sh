#!/usr/bin/env bash
# 一鍵跑完 interview-reel：prep_clips → tts → fetch_broll → build
# 用法：bash run.sh <spec.json> <out_dir> [name]
#   中途要人工補字幕翻譯時，可以單獨跑某一步（見 SKILL.md）。
set -euo pipefail
SPEC=$(realpath "$1"); OUT=$(realpath -m "$2"); NAME=${3:-reel}
S=$(dirname "$(realpath "$0")")
# bash -lc 才會帶到機器環境變數（ELEVENLABS_API_KEY、PEXELS_API_KEY），不要把 key 印出來
source "${OPENMONTAGE_DIR:-$S/../../OpenMontage}/om-env.sh" >/dev/null
mkdir -p "$OUT/work"
cd "$S"
python prep_clips.py --spec "$SPEC" --work "$OUT/work"
python tts.py --spec "$SPEC" --work "$OUT/work"
python fetch_broll.py --spec "$SPEC" --work "$OUT/work"
python build.py --spec "$SPEC" --work "$OUT/work" --out "$OUT" --name "$NAME" --check
python build.py --spec "$SPEC" --work "$OUT/work" --out "$OUT" --name "$NAME"
