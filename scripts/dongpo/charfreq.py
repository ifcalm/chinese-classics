#!/usr/bin/env python3
"""站内语料字频表（供乱码判据用）。"""
import collections, glob, json, re, sys
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
ROOT = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data'
cnt = collections.Counter()
files = glob.glob(ROOT + '/**/*.md', recursive=True)
for j, p in enumerate(files):
    t = open(p, encoding='utf-8', errors='ignore').read()
    m = FM.match(t)
    if m:
        t = t[m.end():]
    cnt.update(HZ.findall(t))
    if j % 8000 == 0:
        sys.stderr.write('\r%d/%d' % (j, len(files)))
sys.stderr.write('\n')
tot = sum(cnt.values())
print('站内语料 %d 汉字 / %d 个不同字' % (tot, len(cnt)))
json.dump({'total': tot, 'freq': dict(cnt)}, open('charfreq.json', 'w', encoding='utf-8'),
          ensure_ascii=False)
