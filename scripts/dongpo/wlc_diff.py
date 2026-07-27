#!/usr/bin/env python3
"""王临川集 vs 四庫本《臨川文集》整卷对齐，取长替换块。

上次失败是因为拿「繁→简转换后的整理本」比四庫本，转换噪声压倒信号。
这次繁对繁 + 异体归一，信噪比完全不同。
"""
import difflib, json, re
import wlc_sweep as W

def main():
    ps = W.pieces()
    siku = {int(k): W.norm(v) for k, v in
            json.load(open('wlc-siku.json', encoding='utf-8')).items()}
    byvol = {}
    for path, vol, title, s in ps:
        byvol.setdefault(vol, []).append((path, title, s))

    blocks = []
    for vol in sorted(byvol):
        a = W.norm(''.join(s for _, _, s in byvol[vol]))
        b = siku.get(vol, '')
        if not b:
            continue
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ratio = sm.quick_ratio()
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'replace' and (i2 - i1) >= 4 and (j2 - j1) >= 4:
                blocks.append((i2 - i1, vol, a[i1:i2], b[j1:j2],
                               a[max(0, i1 - 10):i1], a[i2:i2 + 10]))
    blocks.sort(reverse=True)
    print('长替换块（≥4 字）%d 处，按长度降序:' % len(blocks))
    for n, vol, x, y, pre, post in blocks[:45]:
        print('  卷%-3d %2d字' % (vol, n))
        print('        整理本 …%s【%s】%s…' % (pre, x, post))
        print('        四庫本 【%s】' % y)
    json.dump([[n, v, x, y] for n, v, x, y, _, _ in blocks],
              open('wlc-diff.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
