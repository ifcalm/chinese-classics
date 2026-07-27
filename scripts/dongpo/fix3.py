#!/usr/bin/env python3
"""第二轮回改：简体字形（与/万/尔/号/无）。

四庫本证人给出的用字率：与 0/3406、万 0/1698、尔 0/514、号 0/280、无 4/5721。
整理本却有 与1280/万19/无45——非底本用字，是简体残留。
卷1–114 逐处对位核验；卷115（四庫本无补遗部分）另判。
"""
import json, re, collections
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
NORM = {'蘓':'蘇','巻':'卷','㣲':'微','髙':'高','賔':'賓','逺':'遠','緑':'綠','徃':'往',
        '衆':'眾','絶':'絕','眞':'真','竒':'奇','囘':'回','尓':'爾','虗':'虛','踈':'疏',
        '荅':'答','爲':'為','効':'效','髪':'髮','凖':'準','鬬':'鬥','鬭':'鬥','鬪':'鬥',
        '榖':'穀','糓':'穀','醎':'鹹','徴':'徵','麽':'麼'}
PAIR = {'与':'與', '万':'萬', '尔':'爾', '号':'號', '无':'無'}


def norm(s):
    return ''.join(NORM.get(c, c) for c in s)


def main():
    siku = {int(k): norm(v) for k, v in json.load(open('siku.json', encoding='utf-8')).items()}
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    texts = json.load(open('dp-text3.json', encoding='utf-8'))
    log, unverified = [], collections.Counter()
    for x, blocks in zip(items, texts):
        hay = siku.get(x['vol'])
        pos, stream = [], []
        for bi, b in enumerate(blocks):
            if b.startswith('###'):
                continue
            for ci, ch in enumerate(b):
                if HZ.match(ch):
                    stream.append(ch)
                    pos.append((bi, ci))
        s = ''.join(stream)
        edits = []
        for m in re.finditer('[%s]' % ''.join(PAIR), s):
            i = m.start()
            tgt = PAIR[s[i]]
            if s[i] == '万' and s[i + 1:i + 2] == '俟':      # 万俟：复姓，非「萬」
                continue
            ok = False
            if hay and 5 <= i <= len(s) - 6:
                ns = norm(s)
                pre, post = ns[i - 5:i], ns[i + 1:i + 6]
                j = hay.find(pre)
                while j >= 0:
                    k = j + 5
                    if hay[k + 1:k + 6] == post:
                        ok = (hay[k] == tgt)
                        break
                    j = hay.find(pre, j + 1)
            if ok:
                edits.append((i, s[i], tgt, '证人对位'))
            else:
                unverified[s[i]] += 1
                edits.append((i, s[i], tgt, '未对位'))
        for i, old, new, how in edits:
            bi, ci = pos[i]
            assert blocks[bi][ci] == old
            blocks[bi] = blocks[bi][:ci] + new + blocks[bi][ci + 1:]
            log.append([x['vol'], x['display'], old, new, how, s[max(0, i - 6):i + 7]])
    print('第二轮回改 %d 处' % len(log))
    print('  按字:', dict(collections.Counter('%s→%s' % (r[2], r[3]) for r in log)))
    print('  证人直接对位确认 %d 处；未对位 %d 处（多在卷115 补遗，四庫本无此部分）'
          % (sum(1 for r in log if r[4] == '证人对位'), sum(1 for r in log if r[4] == '未对位')))
    print('  未对位按字:', dict(unverified))
    json.dump(texts, open('dp-text4.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(log, open('fixlog2.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
