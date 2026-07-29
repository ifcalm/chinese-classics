#!/usr/bin/env python3
"""保真校验：落盘正文 vs 回改后的源，只许 delete（篇题转入 title 字段）。"""
import difflib, glob, json, os, re
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/shushu/xiang-shu/huangji-jingshi'
tx = json.load(open('hj-fixed.json', encoding='utf-8'))
src = ''.join(HZ.findall(re.sub(r'\{\{\s*另\s*\|\s*([^|}]*?)\s*\|[^}]*\}\}', r'\1',
              '\n'.join(tx[k] for k in ['皇極經世/卷十一', '皇極經世/卷十二',
                                        '皇極經世/卷十三', '皇極經世/卷十四']))))
got = ''
for p in sorted(glob.glob(BASE + '/*.md')):
    if p.endswith('_index.md'):
        continue
    t = open(p, encoding='utf-8').read()
    got += ''.join(HZ.findall(t[FM.match(t).end():]))
dels, ins, rep = [], [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, got, autojunk=False).get_opcodes():
    if tag == 'delete':
        dels.append(src[i1:i2])
    elif tag == 'insert':
        ins.append(got[j1:j2])
    elif tag == 'replace':
        rep.append((src[i1:i2], got[j1:j2]))
print('源 %d 字 / 落盘 %d 字' % (len(src), len(got)))
print('删 %d  增 %d  换 %d  → %s'
      % (sum(map(len, dels)), sum(map(len, ins)), sum(len(a) for a, _ in rep),
         '✅ 只删不增不换' if not ins and not rep else '❌'))
print('删除项:', sorted(set(dels), key=len, reverse=True)[:8])
if ins or rep:
    print('增:', ins[:5], '换:', rep[:5])
