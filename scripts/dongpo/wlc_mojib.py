#!/usr/bin/env python3
"""王临川集乱码定位（正式）：整卷对齐取替换块，用站内语料二元组支持度判乱码。

判据：整理本一侧几乎无二元组支持（≤0.34）而四庫本一侧成文（≥0.45）→ 乱码。
反之整理本成文者是版本异文或篇序错位，一律不动。
"""
import difflib, glob, json, re
import wlc_sweep as W
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
RAD = re.compile(r'[⺀-⿟]')


def support():
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
    return sup


def main():
    sup = support()

    def sc(x):
        return 1.0 if len(x) < 2 else sum(
            1 for i in range(len(x) - 1) if x[i:i + 2] in sup) / (len(x) - 1)

    ps = W.pieces()
    siku = {int(k): W.norm(v) for k, v in
            json.load(open('wlc-siku.json', encoding='utf-8')).items()}
    byvol = {}
    for path, vol, title, s in ps:
        byvol.setdefault(vol, []).append((path, title, s))

    found = []
    for vol in sorted(byvol):
        # 卷内篇拼流，同时记住每个字属哪篇、篇内第几字
        owner, a = [], []
        for path, title, s in byvol[vol]:
            for i, ch in enumerate(s):
                owner.append((path, title, i))
            a.append(s)
        a = ''.join(a)
        an = W.norm(a)
        b = siku.get(vol, '')
        if not b:
            continue
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                None, an, b, autojunk=False).get_opcodes():
            if tag != 'replace':
                continue
            x, y = a[i1:i2], b[j1:j2]
            # 含康熙部首区字符者直接判乱码，不论长短
            forced = bool(RAD.search(x))
            if not forced and (len(x) < 2 or sc(x) > 0.34 or sc(y) < 0.45):
                continue
            if len(y) > len(x) * 4 + 8:      # 四庫本侧溢出太多，另行人工核
                note = '四庫本侧含篇题溢出，须人工截取'
            else:
                note = ''
            path, title, off = owner[i1]
            found.append({'vol': vol, 'path': path, 'title': title, 'off': off,
                          'bad': x, 'good': y, 'sx': round(sc(x), 2),
                          'sy': round(sc(y), 2), 'note': note,
                          'ctx': a[max(0, i1 - 12):i1] + '【' + x + '】' + a[i2:i2 + 12]})
    print('判定为乱码的替换块 %d 处：' % len(found))
    for f in found:
        print('  卷%-3d %-26s 整%.2f 四%.2f %s' % (f['vol'], f['title'][:24], f['sx'], f['sy'],
                                                 f['note']))
        print('        %s' % f['ctx'])
        print('        四庫本【%s】' % f['good'])
    json.dump(found, open('wlc-mojib.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
