#!/usr/bin/env python3
"""上下文支持度判据：把块连同前后 4 字一起看。

版本异文在上下文里依然成文；乱码会把整句打断。
support(整理本块+上下文) 与 support(四庫本块嵌入同上下文) 之差是决定性的。
"""
import glob, json, re
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)

sup = set()
for p in glob.glob('/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/**/*.md',
                   recursive=True):
    if '/wang-lin-chuan-ji/' in p:
        continue
    t = open(p, encoding='utf-8', errors='ignore').read()
    m = FM.match(t)
    s = ''.join(HZ.findall(t[m.end():] if m else t))
    for i in range(len(s) - 1):
        sup.add(s[i:i + 2])


def sc(x):
    return 1.0 if len(x) < 2 else sum(
        1 for i in range(len(x) - 1) if x[i:i + 2] in sup) / (len(x) - 1)


def main():
    cls = json.load(open('wlc-class.json', encoding='utf-8'))
    rows = []
    for f in cls['moj']:
        ctx = f['ctx']
        pre, mid = ctx.split('【', 1)
        mid, post = mid.split('】', 1)
        pre4, post4 = pre[-4:], post[:4]
        a = sc(pre4 + mid + post4)
        b = sc(pre4 + f['good'] + post4)
        rows.append((round(a, 2), round(b, 2), f))
    rows.sort(key=lambda r: -(r[1] - r[0]))
    strong = [r for r in rows if r[1] - r[0] >= 0.30]
    weak = [r for r in rows if r[1] - r[0] < 0.30]
    print('■ 乱码确凿（换成证人读法后上下文支持度跃升 ≥0.30）%d 处' % len(strong))
    for a, b, f in strong:
        print('  卷%-3d %.2f→%.2f  %s' % (f['vol'], a, b, f['ctx']))
        print('              四庫本【%s】' % f['good'])
    print()
    print('■ 存疑（提升不明显，可能是版本异文或对齐溢出）%d 处' % len(weak))
    for a, b, f in weak:
        print('  卷%-3d %.2f→%.2f  %s  ←四庫【%s】'
              % (f['vol'], a, b, f['ctx'], f['good']))
    json.dump({'strong': [f for _, _, f in strong], 'weak': [f for _, _, f in weak]},
              open('wlc-final.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
