#!/usr/bin/env bash
# contact_sheet.sh in.mp4 out.jpg [cols=4] [rows=3]
set -e
in="$1"; out="$2"; c="${3:-4}"; r="${4:-3}"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
n=$((c*r)); fps=$(python3 -c "print($n/$dur)")
ffmpeg -y -loglevel error -i "$in" -vf "fps=$fps,scale=270:-1,tile=${c}x${r}:padding=6:margin=6" -frames:v 1 -q:v 3 "$out"
echo "$out"
