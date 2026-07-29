#!/usr/bin/env python3
"""《皇极经世》观物内外篇落盘：术数门类新设「象数」组。

只收卷十一至十四（观物内篇 51–62、观物外篇上下），
卷一至十（观物篇 1–50）为元会运世表与律吕声音图，表格渲染方案未定，挂账 #30。
"""
import html, json, os, re, shutil, subprocess
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/shushu'
UA = 'chinese-classics-collector/1.0 (ifcalm.ok@gmail.com)'
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
ORDER = ['皇極經世/卷十一', '皇極經世/卷十二', '皇極經世/卷十三', '皇極經世/卷十四']
OUTER = {'皇極經世/卷十三': '觀物外篇上', '皇極經世/卷十四': '觀物外篇下'}


def clean(t):
    t = re.sub(r'\{\{\s*另\s*\|\s*([^|}]*?)\s*\|[^}]*\}\}', r'\1', t)
    t = re.sub(r'\{\{\s*\*\s*\|\s*([^{}]*?)\s*\}\}', r'\1', t)
    t = re.sub(r'\{\{[^{}]*\}\}', '', t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = re.sub(r"'''|''", '', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'^[ \t　]+', '', t, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def paras(t):
    return [x.strip() for x in re.split(r'\n{2,}', t) if x.strip()]


def to_simp(lines, key):
    p = 'ws-cache/%s.json' % key
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))['t']
    cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA]
    for a, b in [('action', 'parse'), ('text', '\n'.join(lines)), ('contentmodel', 'wikitext'),
                 ('variant', 'zh-hans'), ('prop', 'text'), ('format', 'json'),
                 ('formatversion', '2'), ('wrapoutputclass', '')]:
        cmd += ['--data-urlencode', '%s=%s' % (a, b)]
    cmd.append('https://zh.wikisource.org/w/api.php')
    d = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    t = html.unescape(re.sub(r'<[^>]+>', '', d['parse']['text']))
    out = [re.sub(r'\s*\[(?:编辑|編輯)\]\s*$', '', x).strip() for x in t.split('\n') if x.strip()]
    json.dump({'t': out}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return out


tx = json.load(open('hj-fixed.json', encoding='utf-8'))
items = []
for k in ORDER:
    t = tx[k]
    heads = list(re.finditer(r'^==\s*(.+?)\s*==\s*$', t, re.M))
    if heads:
        for i, m in enumerate(heads):
            e = heads[i + 1].start() if i + 1 < len(heads) else len(t)
            b = paras(clean(t[m.end():e]))
            if b:
                items.append({'title': m.group(1), 'blocks': b})
    else:
        b = paras(clean(t))
        items.append({'title': OUTER[k], 'blocks': b})

simp = to_simp([x['title'] for x in items], 'hj-titles')
assert len(simp) == len(items), (len(simp), len(items))
# ⚠ shushu/xiangshu 已是「相术」组，象数另用带连字符的 slug（仓库惯例），避免撞目录
out = os.path.join(BASE, 'xiang-shu', 'huangji-jingshi')
if os.path.isdir(out):
    shutil.rmtree(out)
os.makedirs(out)
grp = os.path.join(BASE, 'xiang-shu')
if not os.path.exists(os.path.join(grp, '_index.md')):
    open(os.path.join(grp, '_index.md'), 'w', encoding='utf-8').write(
        '---\ntitle: "象数"\nweight: 35\n---\n\n')
open(os.path.join(out, '_index.md'), 'w', encoding='utf-8').write(
    '---\ntitle: "皇极经世"\nweight: 10\nkind: "book"\n'
    'summary: "北宋·邵雍。以元会运世推演天道人事，为象数易学之宗。'
    '本站只收观物内篇（观物篇五十一至六十二）与观物外篇上下，'
    '即全书中论说义理的散文部分；卷一至卷十的元会运世表与律吕声音图涉表格渲染，暂未收录。"\n---\n\n'
    '《皇极经世书》十四卷，本站收卷十一至卷十四。据维基文库整理本收录（繁体），'
    '并以《四库全书》本白文逐字对校。\n')
n = 0
for i, (x, s) in enumerate(zip(items, simp), 1):
    body = '\n\n'.join(x['blocks'])
    open(os.path.join(out, '%02d.md' % i), 'w', encoding='utf-8').write(
        '---\ntitle: "%s"\nweight: %d\n---\n\n%s\n' % (s, i, body))
    n += len(HZ.findall(body))
print('写出 %d 篇 %d 汉字 (%.2f 万) → shushu/xiang-shu/huangji-jingshi' % (len(items), n, n / 10000))
print('篇目:', simp)
