#!/usr/bin/env python3
"""copy_lint: check the Step 3 copy files against the house rules and platform limits before review.

Usage:
  python3 copy_lint.py <YOUR_WORKSPACE>/media-team/03-drafts/<題目>/          # every known copy file, recursively
  python3 copy_lint.py ig_caption.txt threads/1.txt x_post.txt
  python3 copy_lint.py --platform threads some_draft.txt                        # force a platform
  python3 copy_lint.py --fix-invisible <draft dir>                              # also strip invisible characters in place

Which rules apply is decided by file name:
  ig_caption*.txt              -> instagram
  threads*.txt, threads/*.txt  -> threads (a file may hold a chain: separate posts with a line containing only ---)
  x_post*.txt                  -> x (single post)
  x_longpost*.md, x_article*.md, linkedin*.txt, youtube_shorts*.txt, tiktok*.txt -> house rules only
Files under an en/ folder skip the Chinese-only checks (「」 quotes, Taiwan wording, simplified characters).
Text inside 〈…〉 or 《…》 (a quoted original title) is exempt from the simplified-character and wording checks.

ERROR blocks handoff (exit 1). WARN needs a human look. INFO is context. Platform figures and their sources are in
references/meta-platforms.md; the ones marked "reported" are not in Meta's own docs, so they only WARN.
Read-only unless --fix-invisible is given; that only deletes invisible characters (never ZWJ inside an emoji).
"""
import argparse, re, sys, unicodedata
from pathlib import Path

URL = re.compile(r"(?:https?://|www\.)\S+|\b[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.(?:com|net|org|io|ai|tw|dev|app|co|me|gov)(?:/\S*)?", re.I)
HASHTAG = re.compile(r"(?:(?<=\s)|^)#([^\s#.,;:!?@&，。、！？；：]{1,50})")
TITLE = re.compile(r"〈[^〉]*〉|《[^》]*》")
CJK = re.compile(r"[㐀-鿿豈-﫿]")
INVISIBLE = {0x200B, 0x200C, 0x200E, 0x200F, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF, 0x00AD,
             0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0x180E}
ZWJ = 0x200D
# Common simplified-only characters; their Traditional forms differ. Any hit means the text was not converted.
SIMPLIFIED = set("这们说个为么时会对发经现进过还产视频数据见应该没关题问页点击无尽实动头东车长门间马鸟鱼语读写听让认识话请谁调资讯网络软盘线级态区历")
# Mainland wording -> Taiwan wording (house rule: Taiwan wording). Kept to unambiguous pairs.
WORDING = {"視頻": "影片", "短視頻": "短影音", "質量": "品質", "信息": "資訊", "軟件": "軟體", "硬件": "硬體",
           "網絡": "網路", "默認": "預設", "鼠標": "滑鼠", "屏幕": "螢幕", "激活": "啟用", "博主": "創作者",
           "打印": "列印", "服務器": "伺服器", "人工智能": "人工智慧", "算法": "演算法", "芯片": "晶片",
           "代碼": "程式碼", "文檔": "文件", "鏈接": "連結", "點贊": "按讚", "數據庫": "資料庫", "內存": "記憶體",
           "U盤": "隨身碟", "攝像頭": "鏡頭", "高清": "高畫質", "互聯網": "網路"}


def is_emoji(ch):
    cp = ord(ch)
    return (0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or 0x1F1E6 <= cp <= 0x1F1FF
            or 0x2B00 <= cp <= 0x2BFF or cp in (0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D))


def invisible_positions(text):
    out = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        if 0xE0000 <= cp <= 0xE007F or cp in INVISIBLE:
            out.append(i)
        elif cp == ZWJ:  # legitimate only inside an emoji sequence
            prev, nxt = text[i - 1] if i else "", text[i + 1] if i + 1 < len(text) else ""
            if not (prev and nxt and (is_emoji(prev) or ord(prev) == 0xFE0F) and is_emoji(nxt)):
                out.append(i)
    return out


def threads_length(text):
    """Threads: 500 characters, emoji counted by UTF-8 byte length (official docs)."""
    return sum(len(ch.encode("utf-8")) if is_emoji(ch) else 1 for ch in text)


def x_weight(text):
    """X weighted length: URLs 23, Latin and common punctuation 1, CJK/emoji/other 2 (twitter-text v3 ranges)."""
    total, text = 0, unicodedata.normalize("NFC", text)
    for u in URL.findall(text):
        total += 23
        text = text.replace(u, "", 1)
    for ch in text:
        cp = ord(ch)
        if cp in (ZWJ, 0xFE0F) or 0x1F3FB <= cp <= 0x1F3FF:
            continue  # joiners, variation selectors, skin tones don't add
        light = cp <= 4351 or 8192 <= cp <= 8205 or 8208 <= cp <= 8223 or 8242 <= cp <= 8247
        total += 1 if light else 2
    return total


def platform_of(path):
    n, parts = path.name.lower(), [p.lower() for p in path.parts]
    if n.startswith("ig_caption"):
        return "instagram"
    if n.startswith("threads") or "threads" in parts[:-1]:
        return "threads"
    if n.startswith("x_post"):
        return "x"
    if n.startswith(("x_longpost", "x_article", "linkedin", "youtube_shorts", "tiktok")):
        return "house"
    return None


def lint(path, platform, english, fix):
    text = path.read_text(encoding="utf-8")
    issues = []
    E = lambda m: issues.append(("ERROR", m))
    W = lambda m: issues.append(("WARN", m))
    I = lambda m: issues.append(("INFO", m))

    inv = invisible_positions(text)
    if inv:
        if fix:
            keep = set(inv)
            path.write_text("".join(c for i, c in enumerate(text) if i not in keep), encoding="utf-8")
            text = path.read_text(encoding="utf-8")
            I(f"removed {len(inv)} invisible character(s)")
        else:
            E(f"{len(inv)} invisible character(s) (zero-width / direction / tag chars); run with --fix-invisible")
    for i, line in enumerate(text.splitlines(), 1):
        if "\u2014" in line or "\u2015" in line:
            E(f"line {i}: em-dash (house rule: no em-dashes): {line.strip()[:60]!r}")
        if not english and CJK.search(line):
            if re.search(r"[\"“”]", line):
                W(f"line {i}: double quotes in Chinese text; house style uses 「」: {line.strip()[:60]!r}")
            own = TITLE.sub("", line)  # a quoted original title (〈…〉 《…》) keeps its own script and wording
            simp = sorted({c for c in own if c in SIMPLIFIED})
            if simp:
                E(f"line {i}: simplified character(s) {''.join(simp)}; convert to Traditional")
            for k, v in WORDING.items():
                if k in own:
                    W(f"line {i}: 「{k}」 is mainland wording; Taiwan wording is 「{v}」")
    if not english and text.count("「") != text.count("」"):
        W(f"unbalanced 「」 ({text.count('「')} open, {text.count('」')} close)")

    if platform == "instagram":
        n = len(text.strip())
        (E if n > 2200 else I)(f"caption length {n} / 2,200")
        tags = HASHTAG.findall(text)
        if len(tags) > 5:
            W(f"{len(tags)} hashtags; Instagram reported a 5-per-caption cap rolling out from 2025-12-18 (Social Media Today)")
        if URL.search(text):
            I("caption contains a URL; links in IG captions are not clickable")
        preview = text.strip().replace("\n", " ⏎ ")[:125]
        I(f"feed preview, approx. first 125 chars (CJK shows fewer): {preview!r}")
    elif platform == "threads":
        posts = [p.strip() for p in re.split(r"(?m)^\s*---\s*$", text) if p.strip()]
        for k, p in enumerate(posts, 1):
            tag = f"post {k}/{len(posts)}: " if len(posts) > 1 else ""
            n = threads_length(p)
            (E if n > 500 else I)(f"{tag}length {n} / 500 (emoji counted by UTF-8 bytes)")
            links = {u.rstrip(".,)」") for u in URL.findall(p)}
            if len(links) > 5:
                E(f"{tag}{len(links)} unique links; Threads rejects more than 5 (since 2025-12-22)")
            tags = HASHTAG.findall(p)
            if len(tags) > 1:
                W(f"{tag}{len(tags)} in-text topic tags; Threads keeps only the first valid one")
    elif platform == "x":
        n = x_weight(text.strip())
        (E if n > 280 else I)(f"weighted length {n} / 280 (CJK and emoji count 2, URLs 23); longer copy goes in x_longpost.md")
        if URL.search(text):
            E("external link in the X post body; put links (incl. the original-video credit) in the reply (router Step 3)")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--platform", choices=["instagram", "threads", "x", "house"], help="force rules for all files")
    ap.add_argument("--fix-invisible", action="store_true")
    a = ap.parse_args()

    files = []
    for p in map(Path, a.paths):
        if p.is_dir():
            files += [f for f in sorted(p.rglob("*")) if f.is_file() and f.suffix in (".txt", ".md")
                      and (a.platform or platform_of(f.relative_to(p)))]
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"not found: {p}")
    if not files:
        sys.exit("no copy files found (expected ig_caption.txt, threads*.txt, x_post.txt, ...)")

    errors = 0
    for f in files:
        plat = a.platform or platform_of(f) or "house"
        english = "en" in [x.lower() for x in f.parts[:-1]]
        issues = lint(f, plat, english, a.fix_invisible)
        print(f"== {f}  [{plat}{', en' if english else ''}]")
        for level, msg in issues:
            print(f"  {level:5} {msg}")
        errors += sum(1 for lv, _ in issues if lv == "ERROR")
    print(f"{len(files)} file(s), {errors} error(s)", file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
