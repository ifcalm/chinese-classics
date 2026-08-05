# -*- coding: utf-8 -*-
"""简→繁消歧：以站内 8200 万字繁体语料的二元组支持度择形，并做留出验证。

四库本证人是简体，回改需把正字转回繁体，而简→繁是一对多的不安全方向。
故对每个位置的候选繁体形，取与左右邻字二元组支持度最高者；
验证办法是拿维基本自身的干净繁体段折简后再繁化，比对还原率。
"""
import json, random, re, sys
HZ = re.compile(r'[一-鿿]')
BIG = set(json.load(open('oy-bigram.json')))
S2T = {}
for ln in open('STCharacters.txt', encoding='utf-8'):
    if not ln.startswith('#') and '\t' in ln:
        k, v = ln.rstrip('\n').split('\t'); S2T[k] = v.split(' ')


def s2t(s, left='', right=''):
    """逐字择形：与已定的左邻、以及右侧候选，取二元组命中最多者。"""
    out = []
    for i, c in enumerate(s):
        cands = S2T.get(c, [c])
        if len(cands) == 1:
            out.append(cands[0]); continue
        prev = out[-1] if out else (left[-1] if left else '')
        nxt_raw = s[i+1] if i + 1 < len(s) else (right[0] if right else '')
        nxts = S2T.get(nxt_raw, [nxt_raw]) if nxt_raw else ['']
        best, score = cands[0], -1
        for t in cands:
            sc = (1 if prev and prev + t in BIG else 0) + \
                 (1 if any(n and t + n in BIG for n in nxts) else 0)
            if sc > score:
                best, score = t, sc
        out.append(best)
    return ''.join(out)


if __name__ == '__main__':
    sys.path.insert(0, '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/scripts/ouyang')
    from oy_parse import parse
    T2S = {}
    for ln in open('TSCharacters.txt', encoding='utf-8'):
        if not ln.startswith('#') and '\t' in ln:
            k, v = ln.rstrip('\n').split('\t'); T2S[k] = v.split(' ')[0]
    vols, _ = parse()
    random.seed(7)
    pool = [''.join(HZ.findall(''.join(p['lines']))) for v in vols for p in v['pieces']]
    pool = [x for x in pool if len(x) > 200]
    tot = err = 0; bad = []
    for s in random.sample(pool, 220):
        for st in range(0, len(s) - 24, 400):
            seg = s[st:st+24]
            back = s2t(''.join(T2S.get(c, c) for c in seg))
            for a, b in zip(seg, back):
                tot += 1
                if a != b:
                    err += 1
                    if len(bad) < 18: bad.append((a, b, seg))
    print('留出验证：%d 字，还原错 %d，准确率 %.3f%%' % (tot, err, (1-err/tot)*100))
    from collections import Counter
    print('错例 top:', Counter((a,b) for a,b,_ in bad).most_common(10))
