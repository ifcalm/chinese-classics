# -*- coding: utf-8 -*-
"""欧阳修集·篇级对四库本对校。

四库本《文忠集》与维基本卷次编排不同，按卷号对齐会大面积错位，
故改用篇级双锚定位：以篇首 12 字定起点、篇末 12 字定终点，取证人对应窗口再 difflib。
折简仅用于对齐比对（OpenCC TSCharacters），落盘正文仍是底本繁体。
"""
import difflib, json, re, sys
sys.path.insert(0, '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/scripts/ouyang')
from oy_parse import parse

HZ = re.compile(r'[一-鿿]')
T2S = {}
for ln in open('TSCharacters.txt', encoding='utf-8'):
    if not ln.startswith('#') and '\t' in ln:
        k, v = ln.rstrip('\n').split('\t'); T2S[k] = v.split(' ')[0]
simp = lambda s: ''.join(T2S.get(c, c) for c in s)
BIG = set(json.load(open('oy-bigram.json')))
def support(s):
    s = ''.join(HZ.findall(s))
    return 1.0 if len(s) < 2 else sum(1 for i in range(len(s)-1) if s[i:i+2] in BIG)/(len(s)-1)

W = ''.join(HZ.findall(open('oywit/文忠集（宋欧阳修）.txt', encoding='utf-8', errors='replace').read()))
IDX = {}
for i in range(len(W) - 11):
    IDX.setdefault(W[i:i+12], []).append(i)

def locate(key, lo=0):
    v = IDX.get(key)
    if not v: return None
    for x in v:
        if x >= lo: return x
    return v[0]

vols, _ = parse()
moji, stat = [], {'hit':0,'miss':0}
for v in vols:
    for p in v['pieces']:
        s = ''.join(HZ.findall(''.join(p['lines'])))
        if len(s) < 40: continue
        a = simp(s)
        st = None
        for off in range(0, min(len(a)-12, 40), 2):          # 篇首锚（容前置小注）
            st = locate(a[off:off+12]);  st = None if st is None else st-off
            if st is not None: break
        if st is None:
            stat['miss'] += 1; continue
        en = None
        for off in range(0, min(len(a)-12, 40), 2):          # 篇末锚
            e = locate(a[len(a)-12-off:len(a)-off], st)
            if e is not None and st < e < st + len(a)*2 + 200:
                en = e + 12 + off; break
        seg = W[st:en] if en else W[st:st+int(len(a)*1.15)+30]
        stat['hit'] += 1
        sm = difflib.SequenceMatcher(None, a, seg, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != 'replace' or not (2 <= i2-i1 <= 80) or not (2 <= j2-j1 <= 80): continue
            sa, sb = support(s[i1:i2]), support(seg[j1:j2])
            if sa < 0.34 and sb > sa + 0.3:
                moji.append(dict(vol=v['title'], piece=p['title'], wiki=s[i1:i2], wit=seg[j1:j2],
                                 sa=round(sa,2), sb=round(sb,2),
                                 ctx=s[max(0,i1-16):i1]+'〖'+s[i1:i2]+'〗'+s[i2:i2+16]))
json.dump(moji, open('oy-moji2.json','w'), ensure_ascii=False, indent=1)
print('篇级定位：命中 %d，未命中 %d（证人无此篇或异文过大）' % (stat['hit'], stat['miss']))
print('判为乱码的替换块：%d 处，涉及 %d 篇 / %d 卷' % (
    len(moji), len({m['piece'] for m in moji}), len({m['vol'] for m in moji})))
from collections import Counter
print('卷分布:', Counter(m['vol'][:20] for m in moji).most_common(12))
