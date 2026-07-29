#!/usr/bin/env python3
"""单字差异裁定：整理本读法在站内 8064 万字语料中不成词、四庫本读法成词者，判整理本讹。"""
import glob, json, re
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)

sup = set()
for p in glob.glob('/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/**/*.md',
                   recursive=True):
    t = open(p, encoding='utf-8', errors='ignore').read()
    m = FM.match(t)
    s = ''.join(HZ.findall(t[m.end():] if m else t))
    for i in range(len(s) - 1):
        sup.add(s[i:i + 2])

rows = json.load(open('hj-diff.json', encoding='utf-8'))
wrong, ambiguous = [], []
for v, tag, x, y, pre, post in rows:
    if len(x) != 1 or len(y) != 1 or not pre or not post:
        continue
    a2 = [pre[-1] + x, x + post[0]]
    b2 = [pre[-1] + y, y + post[0]]
    sa = sum(1 for k in a2 if k in sup)
    sb = sum(1 for k in b2 if k in sup)
    ctx = pre[-8:] + '〖%s〗' % x + post[:8]
    if sa == 0 and sb == 2:
        wrong.append((v, x, y, ctx))
    elif sa < sb:
        ambiguous.append((v, x, y, ctx, sa, sb))
print('■ 判定整理本讹（本侧两个二元组皆不成词、四庫本侧皆成词）%d 处：' % len(wrong))
for v, x, y, c in wrong:
    print('   %-4s %s→%s   …%s…' % (v, x, y, c))
print()
print('■ 倾向四庫本但不足以定谳（存照不改）%d 处，前 20：' % len(ambiguous))
for v, x, y, c, sa, sb in ambiguous[:20]:
    print('   %-4s %s→%s (%d:%d) …%s…' % (v, x, y, sa, sb, c))
json.dump({'wrong': wrong, 'amb': ambiguous}, open('hj-judge.json', 'w', encoding='utf-8'),
          ensure_ascii=False)
