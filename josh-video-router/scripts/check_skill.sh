#!/usr/bin/env bash
# Check that a skill (and optionally a file inside it) exists under SKILLS_DIR before routing to it.
# Usage: check_skill.sh <skill> [relative/path/in/skill]
#   e.g. check_skill.sh huashu-art-motion templates/data_card_render.py
# Exit 0 = found. Exit 1 = missing: fall back to stock-footage-reel if the topic fits it, otherwise stop and ask the main bot.
set -u
SKILLS_DIR="${SKILLS_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
skill="${1:?usage: check_skill.sh <skill> [path]}"
target="$SKILLS_DIR/$skill${2:+/$2}"
if [ -e "$target" ] && { [ -n "${2:-}" ] || [ -e "$SKILLS_DIR/$skill/SKILL.md" ] || [ -L "$SKILLS_DIR/$skill" ]; }; then
  echo "OK: $target"
else
  echo "MISSING: $target" >&2
  echo "Fallback: use stock-footage-reel if the topic fits it (narrated news / real footage); otherwise stop and ask the main bot." >&2
  exit 1
fi
