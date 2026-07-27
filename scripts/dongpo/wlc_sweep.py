#!/usr/bin/env python3
"""王临川集乱码普查：东坡全集验证过的两步法。

① 二元组普查找候选窗口（站内 8064 万字语料作参照）
② 四庫本《臨川文集》逐窗口锚定核验——锚不上者才是乱码嫌疑
   （不做整书 diff：四庫本异体字会把信号淹掉，这是上次失败的原因）
"""
import difflib, glob, json, os, re, sys
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/wang-lin-chuan-ji'
NORM = {'蘓':'蘇','巻':'卷','㣲':'微','髙':'高','賔':'賓','逺':'遠','緑':'綠','徃':'往',
        '衆':'眾','絶':'絕','眞':'真','竒':'奇','囘':'回','尓':'爾','虗':'虛','踈':'疏',
        '荅':'答','爲':'為','効':'效','髪':'髮','凖':'準','鬬':'鬥','榖':'穀','醎':'鹹',
        '徴':'徵','麽':'麼','刦':'劫','恱':'悅','歴':'歷','冩':'寫','棊':'棋','讐':'讎'}


def norm(s):
    return ''.join(NORM.get(c, c) for c in s)


def pieces():
    out = []
    for p in sorted(glob.glob(BASE + '/*/*.md')):
        if p.endswith('_index.md'):
            continue
        t = open(p, encoding='utf-8').read()
        m = FM.match(t)
        b = t[m.end():] if m else t
        vol = int(os.path.basename(os.path.dirname(p)))
        ti = re.search(r'^title: "(.*)"$', t, re.M)
        out.append((p, vol, ti.group(1) if ti else '', ''.join(HZ.findall(b))))
    return out


def anchored(hay, ctx):
    """窗口在证人里的最佳相似度（前后取锚，异体归一）。"""
    n = len(ctx)
    if not n:
        return 1.0
    cands = set()
    for i in range(max(1, n - 3)):
        sub = ctx[i:i + 4]
        st = 0
        while True:
            j = hay.find(sub, st)
            if j < 0:
                break
            cands.add(max(0, j - i))
            st = j + 1
    if not cands:
        return 0.0
    sm = difflib.SequenceMatcher(None, ctx, '', autojunk=False)
    top = 0.0
    for p in list(cands)[:400]:
        sm.set_seq2(hay[p:p + n])
        r = sm.ratio()
        top = max(top, r)
        if top > 0.98:
            break
    return top


def main():
    ps = pieces()
    siku = {int(k): norm(v) for k, v in json.load(open('wlc-siku.json', encoding='utf-8')).items()}
    own = {}
    for _, _, _, s in ps:
        for i in range(len(s) - 1):
            k = s[i:i + 2]
            own[k] = own.get(k, 0) + 1
    want = set(own)
    seen = set()
    files = glob.glob('/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/**/*.md',
                      recursive=True)
    for j, p in enumerate(files):
        if '/wang-lin-chuan-ji/' in p:
            continue                       # 自身不作参照
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

    cand = []
    for path, vol, title, s in ps:
        run = 0
        for i in range(len(s)):
            if i < len(s) - 1 and s[i:i + 2] in novel:
                run += 1
                continue
            if run >= 3:
                cand.append((run, path, vol, title, i - run, s[max(0, i - run - 10):i + 11]))
            run = 0
    print('候选窗口 %d 处，逐处四庫本核验中…' % len(cand))
    rows = []
    for run, path, vol, title, off, ctx in cand:
        r = anchored(siku.get(vol, ''), norm(ctx))
        rows.append((round(r, 2), run, path, vol, title, ctx))
    rows.sort()
    lo = [x for x in rows if x[0] < 0.55]
    print()
    print('  ≥0.80 证人确认 %d ／ 0.55–0.80 %d ／ <0.55 需人工判 %d'
          % (sum(1 for x in rows if x[0] >= 0.80),
             sum(1 for x in rows if 0.55 <= x[0] < 0.80), len(lo)))
    print()
    print('■ 相似度 <0.55 的 %d 处:' % len(lo))
    for r, run, path, vol, title, ctx in lo:
        print('  %.2f %d连 卷%-3d %-22s …%s…'
              % (r, run, vol, title[:20], ctx))
    json.dump(rows, open('wlc-sweep.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
