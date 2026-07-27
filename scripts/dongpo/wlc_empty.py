#!/usr/bin/env python3
"""8 个空篇处置：2 篇源页在异写标题下存在→补齐；6 篇维基确无→删除挂账。"""
import html, json, os, re, subprocess, ws
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/wang-lin-chuan-ji'
UA = 'chinese-classics-collector/1.0 (ifcalm.ok@gmail.com)'
FILL = [('012/16.md', '招同官遊東園', '招同官游东园'), ('012/20.md', '試茗泉', '试茗泉')]
DROP = [('008/16.md', '山田久欲拆'), ('012/10.md', '同杜使君饮城南'), ('012/11.md', '有感'),
        ('012/15.md', '追送朱氏女弟宿木瘤僧舍'), ('012/18.md', '秋怀'),
        ('012/19.md', '既别羊王二君与同官饮城南')]


def render(wt, key):
    p = 'ws-cache/%s.json' % key
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))['t']
    cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA]
    for a, b in [('action', 'parse'), ('text', wt), ('contentmodel', 'wikitext'),
                 ('prop', 'text'), ('format', 'json'), ('formatversion', '2'),
                 ('wrapoutputclass', '')]:
        cmd += ['--data-urlencode', '%s=%s' % (a, b)]
    cmd.append('https://zh.wikisource.org/w/api.php')
    d = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    json.dump({'t': d['parse']['text']}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return d['parse']['text']


def detag(t):
    t = re.sub(r'<span class="variant-tooltip">.*?</span>', '', t, flags=re.S)
    t = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', t, flags=re.S)
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'</(p|div)>', '\n\n', t)
    t = html.unescape(re.sub(r'<[^>]+>', '', t))
    return re.sub(r'\n{3,}', '\n\n', t).strip()


log = []
for rel, page, simp in FILL:
    wt = ws.wikitext(page)
    m = re.search(r'<onlyinclude>(.*?)</onlyinclude>', wt, re.S)
    body = m.group(1) if m else wt
    body = re.sub(r'\{\{\s*(?:[Hh]eader|北宋作品|PD-old|Textquality)[^{}]*\}\}', '', body)
    lines = [x.strip() for x in detag(render(body, 'wlcfill-' + simp)).split('\n') if x.strip()]
    p = os.path.join(BASE, rel)
    t = open(p, encoding='utf-8').read()
    head = t[:re.match(r'\A---\n.*?\n---\n', t, re.S).end()]
    head = re.sub(r'^title: ".*"$', 'title: "%s"' % simp, head, flags=re.M)
    open(p, 'w', encoding='utf-8').write(head + '\n' + '\n\n'.join(lines) + '\n')
    log.append({'file': rel, 'act': '补齐', 'page': page, 'n': len(lines),
                'why': '原索引标题红链（游/遊、名/茗异写），实页在异写标题下'})
    print('补齐 %s ← %s  %d 段' % (rel, page, len(lines)))
for rel, ti in DROP:
    os.remove(os.path.join(BASE, rel))
    log.append({'file': rel, 'act': '删除', 'title': ti, 'why': '维基无此页，原正文仅红链标题回显，非苏轼…非王安石正文'})
    print('删除 %s（%s）' % (rel, ti))
json.dump(log, open('wlc-empty.json', 'w', encoding='utf-8'), ensure_ascii=False)
