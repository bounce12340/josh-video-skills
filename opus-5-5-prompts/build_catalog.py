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
    f.write('# Opus 5.5 video prompt comparison list\n\nSource: [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos) (fetched 2026-10-21, %d prompts in total). This table does not include prompt text; it lists only titles, categories, links to the author\'s original post, and comparison results. To read a prompt, click "prompt" to go to the source repo.\n\nComparison method: keywords match each prompt to the skills / styles already in this repo and INDEX.md. This is an automatic first pass; check manually before use.\n\n- 重複 (Duplicate): same or nearly the same as a style in an existing skill (named in parentheses), or a duplicate prompt within the source repo.\n- 部分重疊 (Partial overlap): a skill exists for the same kind of workflow (code-rendered motion graphics, explainers, charts), but not the same style.\n- 新 (New): no counterpart in this repo or INDEX.md (mainly Three.js 3D, shaders, interactive games).\n\n'%len(d))
    EN={'新':'New','部分重疊':'Partial overlap','重複':'Duplicate'}
    for lab in ['新','部分重疊','重複']:
        sub=[r for r in rows if r[1]==lab]
        f.write(f'## {lab} / {EN[lab]} ({len(sub)})\n\n| Title | Category | Tech | Author | Matching existing skill | Links |\n|---|---|---|---|---|---|\n')
        for x,_,m in sorted(sub,key=lambda r:(r[0]['category'],r[0]['slug'])):
            t=title(x['slug']).replace('|','／')
            p=' （prompt 不完整）' if x['prompt_partial'] else ''
            f.write(f"| {t}{p} | {CAT[x['category']]} | {', '.join(x['tech_tags'])} | [@{x['author']}]({x['author_url']}) | {m} | [原貼文]({x['post_url']})・[prompt](https://github.com/yihui-dev/awesome-opus5-5-videos/blob/main/prompts/{x['slug']}.md) |\n")
        f.write('\n')

