import json,re,collections,os
import sys
src=sys.argv[1] if len(sys.argv)>1 else 'awesome-opus5-5-videos'
d=json.load(open(f'{src}/data/videos.json'))
def title(slug):
    t=open(f'{src}/prompts/{slug}.md',encoding='utf-8').readline().strip('# \n')
    return t
# (regex, existing skill/style)
DUP=[
 (r'ukiyo|浮世繪|浮世绘','lemo-opuscar ukiyoe'),
 (r'pixel art|8-bit|16-bit|像素','lemo-opuscar pixel-rpg'),
 (r'blueprint|藍圖|蓝图','lemo-opuscar blueprint'),
 (r'ascii|\bcrt\b|terminal|終端|终端','lemo-opuscar ascii-crt'),
 (r'risograph','lemo-opuscar risograph'),
 (r'watercolou?r|水彩','lemo-opuscar watercolor'),
 (r'papercut|paper cut|剪紙|剪纸','lemo-opuscar papercut-red'),
 (r'pop-?up book|立體書|立体书','lemo-opuscar paper-popup'),
 (r'hologra|\bhud\b|全像|全息','lemo-opuscar hologram-hud'),
 (r'isometric|等距','lemo-opuscar iso-infographic'),
 (r'low[- ]?poly','lemo-opuscar lowpoly-island'),
 (r'art deco','lemo-opuscar art-deco'),
 (r'stained glass','lemo-opuscar stained-glass'),
 (r'silent film|默片','lemo-opuscar silent-film'),
 (r'tilt[- ]shift|miniature','lemo-opuscar tilt-shift'),
 (r'\blego\b|brick','lemo-opuscar brick-toy'),
 (r'woodcut|木刻','lemo-opuscar woodcut'),
 (r'engraving|銅版|铜版','lemo-opuscar engraving'),
 (r'halftone','lemo-opuscar halftone-dossier'),
 (r'swiss|kinetic typograph','lemo-opuscar swiss-motion'),
 (r'backrooms','lemo-opuscar backrooms'),
 (r'keynote|product launch|發表會|发布会','lemo-opuscar dark-keynote'),
 (r'ghibli|吉卜力','huashu-art-motion 25_ghibli'),
 (r'whiteboard|白板','simon-skills whiteboard-video／huashu whiteboard'),
 (r'ink wash|水墨|calligraph|書法|书法','huashu-art-motion 水墨／classical-poem-silk-video'),
 (r'3blue1brown|3b1b|manim','huashu-art-motion 3b1b 語法'),
 (r'\bvox\b','huashu-art-motion／vox-director'),
 (r'stick ?(man|figure)|火柴人','stickman-video-director'),
 (r'hand-?drawn|crayon|手繪|手绘|蠟筆|蜡笔','hand-drawn-video-prompts／lemo crayon-book'),
 (r'screen ?record|screencast','screen-record／lemo living-screencast'),
]
PART=[
 (r'chart|graph|data ?vis|dashboard|kpi|statistic|數據|数据|圖表|图表','OpenMontage Remotion 圖表／huashu data_card／lemo dataviz'),
]
rows=[];seen={}
for x in d:
    txt=(title(x['slug'])+' '+x['prompt']).lower()
    norm=re.sub(r'\W+',' ',x['prompt'].lower()).strip()[:200]
    if norm in seen:
        rows.append((x,'重複','來源內重複：同 '+seen[norm]));continue
    seen[norm]=x['slug']
    m=next((s for r,s in DUP if re.search(r,txt)),None)
    if m: rows.append((x,'重複',m));continue
    m=next((s for r,s in PART if re.search(r,txt)),None)
    if m: rows.append((x,'部分重疊',m));continue
    tags=set(x['tech_tags'])
    if x['category'] in('3d','interactive') or tags&{'threejs','shader','webgl','playable','physics'}:
        rows.append((x,'新','無對應（Three.js／shader／互動遊戲類，本 repo 尚無）'));continue
    if x['category']=='explainer':
        rows.append((x,'部分重疊','huashu-art-motion 解說語法／xilo-opus-video'));continue
    rows.append((x,'部分重疊','lemo-opuscar／xilo-opus-video（程式渲染動態圖形，無同款風格）'))
print(collections.Counter(r[1] for r in rows))
print(collections.Counter(r[2] for r in rows if r[1]=='重複' and not r[2].startswith('來源')).most_common())
CAT={'motion':'動態圖形','3d':'3D 場景','explainer':'解說','interactive':'遊戲／互動'}
os.makedirs(os.path.dirname(os.path.abspath(__file__))+'',exist_ok=True)
with open(os.path.dirname(os.path.abspath(__file__))+'/catalog.md','w') as f:
    f.write('# Opus 5.5 影片 prompt 比對清單\n\n來源：[yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)（2026-10-21 抓取，共 %d 筆）。本表不收 prompt 原文，只放標題、分類、作者原文連結和比對結果；要看 prompt 請點「prompt」連到來源 repo。\n\n比對方式：用關鍵字把每筆 prompt 對到本 repo 和 INDEX.md 已收的 skill／風格，屬自動初判，用之前請人工確認。\n\n- 重複：跟現有 skill 的某個風格相同或幾乎相同（括號寫是哪個），或來源 repo 內 prompt 重複。\n- 部分重疊：同一類流程（程式渲染動態圖形、解說、圖表）已有 skill，但沒有同款風格。\n- 新：本 repo 和 INDEX.md 都沒有對應（主要是 Three.js 3D、shader、可互動遊戲）。\n\n'%len(d))
    for lab in ['新','部分重疊','重複']:
        sub=[r for r in rows if r[1]==lab]
        f.write(f'## {lab}（{len(sub)}）\n\n| 標題 | 分類 | 技術 | 作者 | 對應現有 skill | 連結 |\n|---|---|---|---|---|---|\n')
        for x,_,m in sorted(sub,key=lambda r:(r[0]['category'],r[0]['slug'])):
            t=title(x['slug']).replace('|','／')
            p=' （prompt 不完整）' if x['prompt_partial'] else ''
            f.write(f"| {t}{p} | {CAT[x['category']]} | {', '.join(x['tech_tags'])} | [@{x['author']}]({x['author_url']}) | {m} | [原貼文]({x['post_url']})・[prompt](https://github.com/yihui-dev/awesome-opus5-5-videos/blob/main/prompts/{x['slug']}.md) |\n")
        f.write('\n')

