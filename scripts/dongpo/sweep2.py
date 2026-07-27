#!/usr/bin/env python3
"""乱码普查（正片）。

王临川集的教训：单看「二元组罕见」会把苏轼的生僻词汇全部误报。
真正的判据是两条同时成立——
  ① 窗口内相邻二元组连续不见于站内 8064 万字语料；
  ② 窗口内的字**个个都是常用字**（GB/Big5 错转产出的是常用字的乱序，
     而生僻词汇由低频字组成）。
再叠一条独立信号：康熙部首/汉字部件区（U+2E80–U+2FDF）出现即可疑。
"""
import json, re, sys
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
RAD = re.compile(r'[⺀-⿟]')

cf = json.load(open('charfreq.json', encoding='utf-8'))
FREQ, TOT = cf['freq'], cf['total']


def ppm(ch):
    return FREQ.get(ch, 0) / TOT * 1e6


def main():
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    texts = json.load(open('dp-text2.json', encoding='utf-8'))
    streams = [''.join(HZ.findall('\n'.join(b))) for b in texts]

    own = {}
    for s in streams:
        for i in range(len(s) - 1):
            k = s[i:i + 2]
            own[k] = own.get(k, 0) + 1
    want = set(own)
    seen = set()
    import glob
    FM = re.compile(r'\A---\n.*?\n---\n', re.S)
    files = glob.glob('/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/**/*.md',
                      recursive=True)
    for j, p in enumerate(files):
        t = open(p, encoding='utf-8', errors='ignore').read()
        m = FM.match(t)
        if m:
            t = t[m.end():]
        s = ''.join(HZ.findall(t))
        for i in range(len(s) - 1):
            k = s[i:i + 2]
            if k in want:
                seen.add(k)
        if j % 8000 == 0:
            sys.stderr.write('\r参照 %d/%d' % (j, len(files)))
    sys.stderr.write('\n')
    novel = {k for k in want if k not in seen and own[k] == 1}
    print('本书二元组 %d，站内未见且本书孤例 %d' % (len(want), len(novel)))

    hits = []
    for x, s in zip(items, streams):
        run = 0
        for i in range(len(s)):
            if i < len(s) - 1 and s[i:i + 2] in novel:
                run += 1
                continue
            if run >= 3:
                w = s[i - run:i + 1]
                lo = min(ppm(c) for c in w)
                # 常用字下限 ≥5ppm：生僻词汇必含极低频字，乱码不会
                if lo >= 5.0:
                    hits.append((round(lo, 1), run, x['vol'], x['display'],
                                 s[max(0, i - run - 10):i + 11]))
            run = 0
    hits.sort(key=lambda h: -h[1])
    print()
    print('■ 疑似乱码（连续未见二元组 + 全为常用字）%d 处:' % len(hits))
    for lo, r, v, t, ctx in hits[:40]:
        print('  %d连 最低频%6.1fppm 卷%-4d %-16s …%s…' % (r, lo, v, t[:15], ctx))
    print()
    rad = [(x['vol'], x['display'], m.group(0), s[max(0, m.start() - 12):m.start() + 13])
           for x, s in zip(items, streams) for m in RAD.finditer(s)]
    print('■ 康熙部首/部件区字符 %d 处:' % len(rad))
    for v, t, ch, ctx in rad:
        print('   卷%-4d %-18s %r  …%s…' % (v, t[:16], ch, ctx))
    json.dump({'hits': hits, 'rad': rad}, open('sweep2.json', 'w', encoding='utf-8'),
              ensure_ascii=False)


if __name__ == '__main__':
    main()
