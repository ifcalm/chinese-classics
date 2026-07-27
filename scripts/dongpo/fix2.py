#!/usr/bin/env python3
"""简转繁过度转换回改（正式）：现场对位，避免用归一化上下文二次定位。

对每篇：建汉字流 → 流中每个高危字，用前后各 5 字（异体归一后）在同卷四庫本锚定
→ 四庫本同位若给出「简体源字」则回改，并记原文上下文。
"""
import json, re, collections
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
RISK = '鹹幹裏鬥雲餘鐘'
NORM = {'蘓': '蘇', '巻': '卷', '㣲': '微', '髙': '高', '賔': '賓', '逺': '遠', '緑': '綠',
        '徃': '往', '衆': '眾', '絶': '絕', '眞': '真', '竒': '奇', '囘': '回', '尓': '爾',
        '虗': '虛', '踈': '疏', '荅': '答', '爲': '為', '効': '效', '髪': '髮', '凖': '準',
        '鬬': '鬥', '鬭': '鬥', '鬪': '鬥', '榖': '穀', '糓': '穀', '醎': '鹹', '徴': '徵',
        '麽': '麼'}
FIX = {('雲', '云'): '云', ('裏', '里'): '里', ('幹', '干'): '干', ('鹹', '咸'): '咸',
       ('鬥', '斗'): '斗', ('鬥', '㪷'): '斗', ('鐘', '鍾'): '鍾', ('餘', '余'): '余',
       ('幹', '乾'): '乾', ('雲', '謂'): '云', ('幹', '于'): '干'}


def norm(s):
    return ''.join(NORM.get(c, c) for c in s)


def main():
    siku = {int(k): v for k, v in json.load(open('siku.json', encoding='utf-8')).items()}
    sikun = {k: norm(v) for k, v in siku.items()}
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    texts = json.load(open('dp-text2.json', encoding='utf-8'))
    log = []
    for x, blocks in zip(items, texts):
        hay = sikun.get(x['vol'])
        if not hay or x['vol'] == 115:
            continue
        # 汉字流 ← (段号, 段内偏移)
        pos, stream = [], []
        for bi, b in enumerate(blocks):
            if b.startswith('###'):
                continue
            for ci, ch in enumerate(b):
                if HZ.match(ch):
                    stream.append(ch)
                    pos.append((bi, ci))
        s = ''.join(stream)
        ns = norm(s)
        edits = []
        for m in re.finditer('[%s]' % RISK, ns):
            i = m.start()
            if i < 5 or i > len(ns) - 6:
                continue
            pre, post = ns[i - 5:i], ns[i + 1:i + 6]
            j = hay.find(pre)
            while j >= 0:
                k = j + 5
                if hay[k + 1:k + 6] == post:
                    tgt = FIX.get((ns[i], hay[k]))
                    if tgt and tgt != s[i]:
                        edits.append((i, s[i], tgt))
                    break
                j = hay.find(pre, j + 1)
        for i, old, new in edits:
            bi, ci = pos[i]
            assert blocks[bi][ci] == old, (x['vol'], x['display'], old, blocks[bi][ci])
            blocks[bi] = blocks[bi][:ci] + new + blocks[bi][ci + 1:]
            log.append([x['vol'], x['display'], old, new, s[max(0, i - 8):i + 9]])
    print('回改 %d 处' % len(log))
    print(dict(collections.Counter('%s→%s' % (r[2], r[3]) for r in log)))
    print()
    print('抽样 10 处:')
    for r in log[:10]:
        print('   卷%-4d %-18s %s→%s  …%s…' % (r[0], r[1][:16], r[2], r[3], r[4]))
    json.dump(texts, open('dp-text3.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(log, open('fixlog.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
