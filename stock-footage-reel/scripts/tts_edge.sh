#!/usr/bin/env bash
# 備案配音（ElevenLabs 不能用時）：edge-tts 台灣女聲 zh-TW-HsiaoChenNeural。成片 credits 會標成 Edge TTS。
# 用法：tts_edge.sh script.txt vo.mp3 [rate，例如 +5%]
set -euo pipefail
TXT=$(sed -E 's/^\[[0-9]+\][[:space:]]*//' "$1" | sed '/^[[:space:]]*$/d')
edge-tts --voice zh-TW-HsiaoChenNeural --rate "${3:-+0%}" --text "$TXT" --write-media "$2"
echo "$2"
