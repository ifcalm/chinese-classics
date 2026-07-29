#!/usr/bin/env python3
"""C 批乱码普查：非汉字杂讯扫描 + 二元组孤例窗口（东坡/王临川同法）。"""
import glob, json, re, collections, unicodedata
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
PUNCT = set('　，。、；：？！「」『』《》〈〉（）·—…〔〕【】○□●-\n>')
IDSOK = set('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻')
P = json.load(open('c-parsed.json', encoding='utf-8'))

print('■ 非汉字杂讯字符（假名/制表符/全角拉丁/U+FFFD/私用区＝编码损坏铁证）')
tot = 0
for book, d in P.items():
    a = '\n'.join('\n'.join(x['blocks']) for x in d['items'])
    bad = collections.Counter(c for c in a if c not in PUNCT and c not in IDSOK
                              and not HZ.match(c))
    if bad:
        tot += sum(bad.values())
        print('   %-24s %s' % (book, {k: v for k, v in bad.items()}))
print('   合计 %d 处%s' % (tot, ' ✅' if tot == 0 else ''))

print()
print('■ 康熙部首/部件区字符')
rad = [(b, m.group(0)) for b, d in P.items()
       for x in d['items'] for m in re.finditer(r'[⺀-⿟]', '\n'.join(x['blocks']))
       if m.group(0) not in IDSOK]
print('   %d 处%s' % (len(rad), ' ✅' if not rad else ' ' + str(rad[:8])))

print()
print('■ 二元组孤例窗口（站内 8064 万字语料作参照）')
sup = set()
for p in glob.glob('/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/**/*.md',
                   recursive=True):
    t = open(p, encoding='utf-8', errors='ignore').read()
    m = FM.match(t)
    s = ''.join(HZ.findall(t[m.end():] if m else t))
    for i in range(len(s) - 1):
        sup.add(s[i:i + 2])
for book, d in P.items():
    hits = []
    for x in d['items']:
        s = ''.join(HZ.findall('\n'.join(x['blocks'])))
        run = 0
        for i in range(len(s)):
            if i < len(s) - 1 and s[i:i + 2] not in sup:
                run += 1
                continue
            if run >= 4:
                hits.append((run, x['title'], s[max(0, i - run - 8):i + 9]))
            run = 0
    print('   %-24s %d 处' % (book, len(hits)))
    for r, t, c in sorted(hits, reverse=True)[:4]:
        print('        %d连 %-14s …%s…' % (r, t[:12], c))
