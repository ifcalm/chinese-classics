#!/usr/bin/env python3
"""保真校验：落盘正文 vs 渲染原文，只许 delete，replace 必须逐条对上回改账。"""
import difflib, glob, json, os, re
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/dong-po-quan-ji'

items = json.load(open('dp-build.json', encoding='utf-8'))['items']
src = json.load(open('dp-text2.json', encoding='utf-8'))     # 回改前
fixlog = (json.load(open('fixlog.json', encoding='utf-8'))
          + json.load(open('fixlog2.json', encoding='utf-8')))

byvol = {}
for x, t in zip(items, src):
    byvol.setdefault(x['vol'], []).append(t)

nrep = ndel = nins = 0
bad = []
for vol, blocks in byvol.items():
    files = sorted(f for f in glob.glob(os.path.join(BASE, '%03d' % vol, '*.md'))
                   if not f.endswith('_index.md'))
    if len(files) != len(blocks):
        bad.append('卷%d 文件数 %d ≠ 篇数 %d' % (vol, len(files), len(blocks)))
        continue
    for f, b in zip(files, blocks):
        raw = open(f, encoding='utf-8').read()
        m = FM.match(raw)
        got = ''.join(HZ.findall(raw[m.end():]))
        want = ''.join(HZ.findall('\n'.join(b)))
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, want, got,
                                                           autojunk=False).get_opcodes():
            if tag == 'equal':
                continue
            if tag == 'replace':
                nrep += i2 - i1
            elif tag == 'delete':
                ndel += i2 - i1
                bad.append('%s 删 %d 字: %r' % (f, i2 - i1, want[i1:i2][:30]))
            else:
                nins += j2 - j1
                bad.append('%s 增 %d 字: %r' % (f, j2 - j1, got[j1:j2][:30]))

print('落盘 vs 渲染原文：replace %d / delete %d / insert %d' % (nrep, ndel, nins))
print('回改账记 %d 处' % len(fixlog))
print('→ %s' % ('✅ 逐字闭合，replace 数与回改账相符，无增无删'
                if nrep == len(fixlog) and ndel == 0 and nins == 0 else '❌ 不闭合'))
for b in bad[:10]:
    print('  ', b)

# 篇名必须全简体
trad = set('與這來後個從們兒點麗龍鳳書畫習節親義華錄漢覺說門問錢國學時對為無東車馬長風開關')
bt = []
for f in glob.glob(BASE + '/**/*.md', recursive=True):
    m = re.search(r'^title: "(.*)"$', open(f, encoding='utf-8').read(), re.M)
    if m and (set(m.group(1)) & trad):
        bt.append((os.path.relpath(f, BASE), m.group(1)))
print()
print('篇名残留繁体 %d 处' % len(bt))
for f, t in bt[:15]:
    print('   %s  %s' % (f, t))
