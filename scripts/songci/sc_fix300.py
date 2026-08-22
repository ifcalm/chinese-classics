# -*- coding: utf-8 -*-
"""《宋詞三百首》缺字回補——以 `宋词/ci.song.*.json` 為證人。

**病灶在上游**：chinese-poetry 的 `宋词/宋词三百首.json` 掉了生僻字——
「風銷焰蠟，露烘爐」少「浥」、「綠樹聽鵜」少「鴂」、「朱鈿寶」少「玦」。
站內是忠實照錄的，不是本站解析丟的。同一項目的 `ci.song.*.json` 收有同一批詞
且字是全的（站內二十五部詞集正出自它），故可作證人逐字回補。

**只補、不改**：對每一篇取證人側最相似者，逐個 opcode 檢查。
- `insert`（證人有、本篇無）→ 補。這就是掉字。
- `replace` → **一概不動**。全批只有六種，都是字形或異文，非掉字：
  後→后 ×39（本篇用的「後」反倒是正字）、颸→飔、攲→敧、茜→蒨、
  蒙蒙→濛濛、蕭瑟→瀟灑（蘇軾《八聲甘州》真異文）。且六種**皆等長**，
  不影響插入點的位置換算。
- `delete`（本篇有、證人無）→ **整篇跳過**。那說明配錯了對，或證人才是殘的。

**回補位置靠索引回映**：抽漢字流時同步記下每個漢字在原文裏的偏移，
補字時按這張表插回去，標點與分段一字不動。

**⚠ 掉的字落在標點兩側時，插在哪一邊要看證人**。漢字流只告訴你它在「前一個漢字」
與「後一個漢字」之間，可那中間往往夾著逗號或句號，插錯邊就串了句：
《水龍吟》的「鱠」在證人裏作「休說鱸魚堪鱠。」，該貼在句末句號**之前**；
《鶯啼序》的「嚲」在證人裏作「尚染鮫綃，嚲鳳迷歸」，該落在逗號**之後**。
判據取證人裏該字的緊鄰字元：前鄰是標點就插到目標的標點之後，後鄰是標點就插到之前。
"""
import json, glob, os, re, sys, difflib, collections

SRC = os.environ.get('CP_DIR', '')
DEST = 'base-data/literature/song-ci-san-bai-shou'
HAN = re.compile(r'[一-鿿㐀-䶿]')
PUNCT = re.compile(r'[。，、；：？！「」『』（）\n\u3000 ]')


def han_index(t):
    """→ (漢字流, [每個漢字在 t 裏的偏移])"""
    chars, pos = [], []
    for i, ch in enumerate(t):
        if HAN.match(ch):
            chars.append(ch); pos.append(i)
    return ''.join(chars), pos


def witnesses():
    fs = glob.glob(os.path.join(SRC, '宋词', 'ci.song.*.json'))
    if not fs:
        sys.exit('未找到 ci.song.*.json，请设 CP_DIR')
    out = []
    for f in sorted(fs):
        for p in json.load(open(f, encoding='utf-8')):
            raw = '\n'.join(p.get('paragraphs', []))
            h, hp = han_index(raw)
            if len(h) >= 20:
                out.append(((p.get('author') or '').strip(),
                            (p.get('rhythmic') or '').strip(), h, raw, hp))
    return out


def main(apply=False):
    wit = witnesses()
    # 步長 1 的 6-gram 索引：掉一個字會讓其後全部位移，步長大於 1 就對不上
    idx = collections.defaultdict(set)
    for i, (_, _, h, _, _) in enumerate(wit):
        for st in range(0, min(len(h) - 5, 80)):
            idx[h[st:st + 6]].add(i)

    fixed, skipped, untouched, nochange = [], [], [], 0
    added = collections.Counter()
    for f in sorted(glob.glob(os.path.join(DEST, '**', '*.md'), recursive=True)):
        if f.endswith('_index.md'):
            continue
        raw = open(f, encoding='utf-8').read()
        head, body = raw.split('---', 2)[1], raw.split('---', 2)[2]
        h, pos = han_index(body)
        if not h:
            continue
        cand = set()
        for st in range(0, min(len(h) - 5, 80)):
            cand |= idx.get(h[st:st + 6], set())
        best, br = None, 0
        for i in cand:
            r = difflib.SequenceMatcher(None, h, wit[i][2], autojunk=False).ratio()
            if r > br:
                br, best = r, wit[i]
        if not best or br < 0.85:
            continue
        ops = [o for o in difflib.SequenceMatcher(None, h, best[2], autojunk=False)
               .get_opcodes() if o[0] != 'equal']
        if not ops:
            nochange += 1; continue
        if any(o[0] == 'delete' for o in ops):
            skipped.append((f, best[0], [(o[0], h[o[1]:o[2]], best[2][o[3]:o[4]])
                                         for o in ops][:3]))
            continue
        if any(o[0] == 'replace' and (o[2] - o[1]) != (o[4] - o[3]) for o in ops):
            skipped.append((f, best[0], [('不等长replace', h[o[1]:o[2]],
                                          best[2][o[3]:o[4]]) for o in ops][:3]))
            continue
        kept = [(o[0], h[o[1]:o[2]], best[2][o[3]:o[4]])
                for o in ops if o[0] == 'replace']
        ops = [o for o in ops if o[0] == 'insert']
        if not ops:
            nochange += 1
            if kept:
                untouched.append((f, best[0], kept))
            continue
        # 從後往前插，免得前面的插入把後面的偏移推掉
        wraw, whp = best[3], best[4]
        new = body
        got = []
        for tag, i1, i2, j1, j2 in reversed(ops):
            ins = best[2][j1:j2]
            prev_c = wraw[whp[j1] - 1] if j1 < len(whp) and whp[j1] > 0 else ''
            nxt_i = whp[j2 - 1] + 1 if j2 - 1 < len(whp) else len(wraw)
            next_c = wraw[nxt_i] if nxt_i < len(wraw) else ''
            if PUNCT.match(prev_c):                       # 證人裏前鄰是標點 → 插在標點之後
                at = pos[i1] if i1 < len(pos) else len(new)
            elif PUNCT.match(next_c) and i1 > 0:          # 後鄰是標點 → 插在標點之前
                at = pos[i1 - 1] + 1
            else:
                at = pos[i1] if i1 < len(pos) else len(new)
            new = new[:at] + ins + new[at:]
            got.append(ins)
        for ins in got:
            for c in ins:
                added[c] += 1
        fixed.append((f, best[0], ''.join(reversed(got))))
        if apply:
            open(f, 'w', encoding='utf-8').write('---%s---%s' % (head, new))

    print('回补 %d 篇 · %d 字%s；无须动 %d 篇（其中 %d 篇只有字形/异文差异，一律不动）；'
          '跳过 %d 篇'
          % (len(fixed), sum(added.values()), '' if apply else '（预演）',
             nochange, len(untouched), len(skipped)))
    print('补入的字：%s' % ''.join('%s×%d ' % (k, v) for k, v in added.most_common()))
    for f, au, ins in fixed:
        print('  + %-6s %-42s %s' % (au, f.replace(DEST + '/', ''), ins))
    for f, au, ops in skipped:
        print('  ‖ 跳过 %-6s %-38s %s' % (au, f.replace(DEST + '/', ''), ops))
    rep = collections.Counter()
    for _, _, kept in untouched + [(a, b, [o for o in c if o[0] == 'replace'])
                                   for a, b, c in []]:
        for t, x, y in kept:
            rep[(x, y)] += 1
    if rep:
        print('  不动的字形/异文：%s'
              % ' '.join('%s→%s×%d' % (a, b, n) for (a, b), n in rep.most_common()))


if __name__ == '__main__':
    main('--apply' in sys.argv)
