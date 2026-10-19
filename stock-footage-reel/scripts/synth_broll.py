#!/usr/bin/env python3
"""本機產生的抽象 B-roll（沒有授權問題），找不到合適素材時的備案。
kind: code（深色編輯器捲動程式碼）、terminal（終端機逐行輸出）、grid（暗色資料格線脈衝）
用法：python3 synth_broll.py code 6 out.mp4
"""
import random, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image, ImageDraw, ImageFont

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
CODE = '''class AgentPolicy:
    def __init__(self, scopes, audit_log):
        self.scopes = set(scopes)
        self.audit = audit_log
    def allow(self, action, resource):
        ok = (action, resource.kind) in self.scopes
        self.audit.write(action=action, resource=resource.id, allowed=ok)
        return ok
def run_task(agent, task, policy, kill_switch):
    for step in agent.plan(task):
        if kill_switch.engaged():
            return Halt("human stop")
        if not policy.allow(step.action, step.resource):
            escalate(step, reason="out of scope")
            continue
        result = sandbox.execute(step)
        verify(result, independent=True)
    return Done()
'''.splitlines()
KW = ("class", "def", "return", "if", "for", "in", "not", "continue", "self")


def _font(sz):
    try:
        return ImageFont.truetype(MONO, sz)
    except Exception:
        return ImageFont.load_default()


def make(kind, dur, out, seed=0, W=1080, H=1920, fps=30):
    rnd = random.Random(seed)
    tmp = Path(out).with_suffix(".png")
    if kind in ("code", "terminal"):
        f = _font(40)
        lines = []
        for _ in range(6):
            lines += CODE if kind == "code" else [f"$ agent run --task {rnd.randint(100,999)}", "  [audit] step ok", "  [policy] denied: write prod-db",
                                                    "  [human] approval required", "  [audit] logged"]
        lh = 58
        img = Image.new("RGB", (W, lh * len(lines) + H), (12, 16, 22))
        d = ImageDraw.Draw(img)
        for i, ln in enumerate(lines):
            y = 160 + i * lh
            d.text((40, y), f"{i % 99 + 1:>3}", font=f, fill=(70, 80, 95))
            x = 150
            for tok in ln.replace("(", " ( ").replace(")", " ) ").split(" "):
                col = (120, 200, 255) if tok in KW else (230, 170, 90) if tok.startswith('"') else (200, 210, 220)
                if "denied" in ln or "approval" in ln:
                    col = (240, 120, 100)
                d.text((x, y), tok, font=f, fill=col)
                x += d.textlength(tok + " ", font=f)
        img.save(tmp)
        speed = 70  # px/s
        vf = f"crop={W}:{H}:0:'min(ih-{H},t*{speed})',format=yuv420p"
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(tmp), "-t", f"{dur:.2f}",
               "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out]
    else:  # grid
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
               f"color=c=0x0b1118:s={W}x{H}:d={dur:.2f}:r={fps}", "-vf",
               "drawgrid=w=90:h=90:t=1:c=0x2a6f80@0.5,noise=alls=8:allf=t,format=yuv420p",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", out]
    subprocess.run(cmd, check=True)
    tmp.unlink(missing_ok=True)
    return out


if __name__ == "__main__":
    make(sys.argv[1], float(sys.argv[2]), sys.argv[3])
