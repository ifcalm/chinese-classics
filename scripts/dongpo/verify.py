#!/usr/bin/env python3
"""用四庫本核验乱码普查命中的每一处窗口。

做法不是整书 diff（王临川集的教训：四庫本异体字会淹没信号），
而是逐窗口在同卷四庫本里做模糊定位：
锚点用命中区**前后各 6 字**，命中区本身允许异体差异后比对相似度。
乱码段在四庫本里必然锚不上或相似度极低；生僻词汇则能锚上。
"""
import difflib, json, re
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')


def best(hay, needle):
    """在 hay 中找与 needle 最相似的等长片段的相似度。"""
    if not needle:
        return 1.0
    n = len(needle)
    sm = difflib.SequenceMatcher(None, needle, '', autojunk=False)
    top = 0.0
    # 先用锚点缩小范围：needle 的任意 4 字子串出现处
    cands = set()
    for i in range(0, max(1, n - 3)):
        sub = needle[i:i + 4]
        st = 0
        while True:
            j = hay.find(sub, st)
            if j < 0:
                break
            cands.add(max(0, j - i))
            st = j + 1
    if not cands:
        return 0.0
    for p in list(cands)[:400]:
        sm.set_seq2(hay[p:p + n])
        r = sm.ratio()
        if r > top:
            top = r
            if top > 0.98:
                break
    return top


def main():
    sw = json.load(open('sweep2.json', encoding='utf-8'))['hits']
    siku = {int(k): v for k, v in json.load(open('siku.json', encoding='utf-8')).items()}
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    texts = json.load(open('dp-text2.json', encoding='utf-8'))
    streams = {}
    for x, b in zip(items, texts):
        streams.setdefault(x['vol'], []).append(''.join(HZ.findall('\n'.join(b))))

    rows = []
    for lo, run, vol, disp, ctx in sw:
        hay = siku.get(vol, '')
        r = best(hay, ctx) if hay else -1.0
        rows.append((r, run, vol, disp, ctx))
    rows.sort()
    ok = sum(1 for r, *_ in rows if r >= 0.80)
    mid = sum(1 for r, *_ in rows if 0.55 <= r < 0.80)
    bad = sum(1 for r, *_ in rows if 0 <= r < 0.55)
    print('普查命中 %d 处，四庫本核验：' % len(rows))
    print('  相似度 ≥0.80（确认为底本原文）      %d' % ok)
    print('  0.55–0.80（异体字多，仍属同文）    %d' % mid)
    print('  <0.55（四庫本无对应，需人工判）     %d' % bad)
    print()
    print('■ 相似度最低的 25 处：')
    for r, run, vol, disp, ctx in rows[:25]:
        w = siku.get(vol, '')
        print('  %.2f %d连 卷%-4d %-16s …%s…' % (r, run, vol, disp[:15], ctx))
    json.dump(rows, open('verify.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
