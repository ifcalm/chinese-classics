#!/usr/bin/env python3
"""简转繁过度转换排查：拿四庫本逐字对位核验高危字。

高危字＝繁简一对多里「转错方向」的那一半（鹹/幹/髮/裏/鬥/雲/餘…）。
做法：把整理本每处高危字的前后 5 字作锚，在同卷四庫本定位，
读出四庫本同位置的字；不同则列为候选（四庫本异体字先归一）。
"""
import json, re, collections
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
RISK = '鹹幹髮裏鬥雲餘穀準鐘嚮彊瞭儘徵麼纔閒'
# 四庫本惯用异体，归一后再比，免得整页都是假阳性
NORM = {'蘇': '蘇', '蘓': '蘇', '巻': '卷', '㣲': '微', '髙': '高', '賔': '賓', '逺': '遠',
        '緑': '綠', '徃': '往', '衆': '眾', '絶': '絕', '眞': '真', '竒': '奇', '囘': '回',
        '尓': '爾', '虗': '虛', '槖': '橐', '踈': '疏', '荅': '答', '爲': '為', '効': '效'}


def norm(s):
    return ''.join(NORM.get(c, c) for c in s)


def main():
    siku = {int(k): norm(v) for k, v in json.load(open('siku.json', encoding='utf-8')).items()}
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    texts = json.load(open('dp-text2.json', encoding='utf-8'))
    cand = collections.Counter()
    detail = []
    for x, b in zip(items, texts):
        if x['vol'] == 115:
            continue          # 四庫本卷115 不含补遗部分，无从对位
        s = ''.join(HZ.findall('\n'.join(b)))
        hay = siku.get(x['vol'], '')
        if not hay:
            continue
        ns = norm(s)
        for m in re.finditer('[%s]' % RISK, ns):
            i = m.start()
            if i < 5 or i > len(ns) - 6:
                continue
            pre, post = ns[i - 5:i], ns[i + 1:i + 6]
            j = hay.find(pre)
            while j >= 0:
                k = j + 5
                if hay[k + 1:k + 6] == post:
                    if hay[k] != ns[i]:
                        cand[(ns[i], hay[k])] += 1
                        detail.append((x['vol'], x['display'], ns[i], hay[k],
                                       ns[max(0, i - 8):i + 9]))
                    break
                j = hay.find(pre, j + 1)
    print('前后各 5 字都对上、独该字相异的处所 %d:' % len(detail))
    for (a, b), n in cand.most_common(30):
        print('   整理本 %s ← 四庫本 %s   × %d' % (a, b, n))
    print()
    for v, t, a, b, ctx in detail[:40]:
        print('   卷%-4d %-18s %s→%s  …%s…' % (v, t[:16], a, b, ctx))
    json.dump(detail, open('overconv.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
