#!/usr/bin/env python3
"""按回改表改 base-data/literature/wang-lin-chuan-ji/，逐处校验唯一命中。"""
import glob, json, os, re
import wlc_fixtable as T
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/wang-lin-chuan-ji'
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
RAD = re.compile(r'[⺀-⿟]')

# 两处康熙部首残字，四庫本核出真字（不在替换块表内，单字对位）
SINGLE = [(65, '抱衾與⺶', '抱衾與裯', '《詩·召南·小星》「抱衾與裯」'),
          (72, '鴟巍芬砸磐⺶非', '鴟鴞以遺王亦非', '与卷72「巍芬砸磐」同段，⺶ 系同一次损坏残留')]

log, miss = [], []
for vol, bad, good, why in T.FIX:
    d = os.path.join(BASE, '%03d' % vol)
    hits = []
    for p in sorted(glob.glob(d + '/*.md')):
        if p.endswith('_index.md'):
            continue
        t = open(p, encoding='utf-8').read()
        m = FM.match(t)
        head, body = t[:m.end()], t[m.end():]
        n = body.count(bad)
        if n:
            hits.append((p, head, body, n))
    if not hits:
        miss.append((vol, bad, '未找到'))
        continue
    tot = sum(n for *_, n in hits)
    for p, head, body, n in hits:
        ti = re.search(r'^title: "(.*)"$', head, re.M)
        open(p, 'w', encoding='utf-8').write(head + body.replace(bad, good))
        log.append({'vol': vol, 'file': os.path.relpath(p, BASE), 'title': ti.group(1),
                    'bad': bad, 'good': good, 'n': n, 'why': why})
    if tot > 1:
        log[-1]['multi'] = tot

for vol, bad, good, why in SINGLE:
    for p in sorted(glob.glob(os.path.join(BASE, '%03d' % vol) + '/*.md')):
        t = open(p, encoding='utf-8').read()
        if bad in t:
            m = FM.match(t)
            ti = re.search(r'^title: "(.*)"$', t[:m.end()], re.M)
            open(p, 'w', encoding='utf-8').write(t[:m.end()] + t[m.end():].replace(bad, good))
            log.append({'vol': vol, 'file': os.path.relpath(p, BASE), 'title': ti.group(1),
                        'bad': bad, 'good': good, 'n': 1, 'why': why})
            break
    else:
        miss.append((vol, bad, '未找到'))

print('回改落地 %d 处（涉 %d 个文件）' % (sum(r['n'] for r in log), len({r['file'] for r in log})))
if miss:
    print('!! 未命中 %d 条: %s' % (len(miss), miss))
left = [(p, m.group(0)) for p in glob.glob(BASE + '/*/*.md')
        for m in RAD.finditer(open(p, encoding='utf-8').read())]
print('康熙部首区残留: %d 处 %s' % (len(left), left))
json.dump(log, open('wlc-applied.json', 'w', encoding='utf-8'), ensure_ascii=False)
for r in log[:8]:
    print('   卷%-3d %-14s %s→%s  %s' % (r['vol'], r['file'], r['bad'], r['good'], r['why']))
