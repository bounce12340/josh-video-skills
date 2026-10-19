#!/usr/bin/env python3
"""第 2 步：旁白配音。ElevenLabs Sarah Explains（Nhs7eitvQWFTQBsf0yiT），用 OpenMontage 的 elevenlabs_tts 工具，一行一個檔。
同一句文字＋同一個聲音只會送一次（以文字雜湊快取在 cache/tts/），改稿只會重配改到的那幾行，不會重複扣點。

用法（先 source OpenMontage/om-env.sh，ELEVENLABS_API_KEY 由機器環境變數提供，不要印出來）：
  python tts.py --spec spec.json --work WORK [--dry-run]
輸出 WORK/tts/manifest.json：每行的音檔路徑與秒數。
"""
import argparse, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ir_common import CACHE, VOICE_ID, VOICE_MODEL, load_json, save_json, sha, narr_lines, probe_duration  # noqa

import os  # noqa: E402
OM = Path(os.environ.get("OPENMONTAGE_DIR", Path(__file__).resolve().parents[2] / "OpenMontage"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True); ap.add_argument("--work", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    spec = load_json(a.spec); work = Path(a.work); (work / "tts").mkdir(parents=True, exist_ok=True)
    v = spec.get("voice", {})
    voice_id = v.get("voice_id", VOICE_ID); model = v.get("model", VOICE_MODEL)
    settings = {k: v[k] for k in ("stability", "similarity_boost", "style", "speed") if k in v}
    todo, manifest = [], []
    for si, seg in enumerate(spec["segments"]):
        if seg["type"] == "clip":
            continue
        nl = narr_lines(seg)
        for li, (text, _, _) in enumerate(nl):
            key = sha(f"{voice_id}|{model}|{sorted(settings.items())}|{text}")
            p = CACHE / "tts" / f"{key}.mp3"
            manifest.append({"seg": si, "line": li, "text": text, "path": str(p)})
            if not p.exists():
                ctx = {}
                if li > 0: ctx["previous_text"] = nl[li - 1][0]
                if li + 1 < len(nl): ctx["next_text"] = nl[li + 1][0]
                todo.append((text, p, ctx))
    chars = sum(len(t[0]) for t in todo)
    print(f"{len(manifest)} lines, {len(todo)} new ({chars} characters to send)")
    if a.dry_run:
        for t, *_ in todo: print("  +", t)
        return
    if todo:
        sys.path.insert(0, str(OM))
        from tools.audio.elevenlabs_tts import ElevenLabsTTS
        tool = ElevenLabsTTS()
        for t, p, ctx in todo:
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".part.mp3")
            r = tool.execute(dict(text=t, voice_id=voice_id, model_id=model, output_path=str(tmp), **settings, **ctx))
            if not getattr(r, "success", False) or not tmp.exists():
                raise SystemExit(f"ElevenLabs failed: {getattr(r, 'error', r)}\n備案：用 user-Elevenlabs 連接器 creative_generate_speech "
                                 f"（generations_count 1）產生這一句，存成 {p}")
            shutil.move(tmp, p)
            print("  voiced:", t[:70])
    for m in manifest:
        m["dur"] = round(probe_duration(m["path"]), 3)
    save_json(work / "tts" / "manifest.json", {"voice": {"provider": "ElevenLabs", "voice": f"Sarah Explains ({voice_id})",
                                                          "model": model}, "lines": manifest})
    print("total narration", round(sum(m["dur"] for m in manifest), 1), "s")


if __name__ == "__main__":
    main()
