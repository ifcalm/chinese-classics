#!/usr/bin/env python3
"""落盘 base-data/literature/dong-po-quan-ji/：一卷一子目录、一篇一文件。

篇名一律简体（站内铁律），正文保持底本繁体。
"""
import json, os, re, shutil, subprocess, html
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/dong-po-quan-ji'
UA = 'chinese-classics-collector/1.0 (ifcalm.ok@gmail.com)'
CN = '〇一二三四五六七八九'


def cn_num(k):
    if k == 100:
        return '一百'
    if k > 100:
        r = '一百'
        k -= 100
        if k >= 10:
            r += ('十' if k // 10 == 1 else CN[k // 10] + '十')
            k %= 10
        return r + (CN[k] if k else '')
    if k < 10:
        return CN[k]
    if k < 20:
        return '十' + (CN[k % 10] if k % 10 else '')
    return CN[k // 10] + '十' + (CN[k % 10] if k % 10 else '')


def to_simp(lines, key):
    """篇名转简体：用维基 LanguageConverter，variant 必须 zh-hans。"""
    p = 'ws-cache/%s.json' % key
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))['t']
    cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA]
    for a, b in [('action', 'parse'), ('text', '\n'.join(lines)), ('contentmodel', 'wikitext'),
                 ('variant', 'zh-hans'), ('prop', 'text'), ('format', 'json'),
                 ('formatversion', '2'), ('wrapoutputclass', '')]:
        cmd += ['--data-urlencode', '%s=%s' % (a, b)]
    cmd.append('https://zh.wikisource.org/w/api.php')
    d = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    t = html.unescape(re.sub(r'<[^>]+>', '', d['parse']['text']))
    out = [x for x in t.split('\n') if x.strip()]
    json.dump({'t': out}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return out


def clean_title(disp):
    """索引显示名 → 篇题：{{*|（…）}} 小注并入括号，去链接与残标记。"""
    t = re.sub(r'\{\{\s*\*\s*\|\s*(.*?)\s*\}\}', r'\1', disp)
    t = re.sub(r'\{\{\s*-\s*\|\s*(.*?)\s*\}\}', r'（\1）', t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = re.sub(r"'''|''", '', t)
    t = t.replace('‎', '').strip()
    return re.sub(r'\s+', '', t)


def main():
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    texts = json.load(open('dp-text4.json', encoding='utf-8'))
    titles = [clean_title(x['display']) for x in items]
    simp = []
    for i in range(0, len(titles), 150):
        simp += to_simp(titles[i:i + 150], 'dp-simp-%04d' % i)
    if len(simp) != len(titles):
        raise SystemExit('!! 转简条数 %d ≠ %d' % (len(simp), len(titles)))

    if os.path.isdir(BASE):
        shutil.rmtree(BASE)
    byvol = {}
    for x, t, s in zip(items, texts, simp):
        byvol.setdefault(x['vol'], []).append((s, t, x))

    nfile = nchar = 0
    for vol in sorted(byvol):
        d = os.path.join(BASE, '%03d' % vol)
        os.makedirs(d)
        groups = [x['group'] for _, _, x in byvol[vol] if x.get('group')]
        label = '卷' + cn_num(vol)
        if groups:
            # 体裁组名同样须简体（站内铁律：标题一律简体）
            gs = to_simp(list(dict.fromkeys(groups)), 'dp-grp-%03d' % vol)
            label += '·' + '、'.join(gs)
        open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
            '---\ntitle: "%s"\nweight: %d\n---\n\n' % (label, vol))
        width = max(2, len(str(len(byvol[vol]))))
        for i, (s, blocks, x) in enumerate(byvol[vol], 1):
            body = '\n\n'.join(blocks)
            open(os.path.join(d, '%0*d.md' % (width, i)), 'w', encoding='utf-8').write(
                '---\ntitle: "%s"\nweight: %d\n---\n\n%s\n' % (s.replace('"', '”'), i, body))
            nfile += 1
            nchar += len(re.findall(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]', body))
    open(os.path.join(BASE, '_index.md'), 'w', encoding='utf-8').write(
        '---\ntitle: "东坡全集"\nweight: 1036\nkind: "book"\n'
        'summary: "北宋·苏轼诗文全集，唐宋八大家之一。一百十五卷，据维基文库整理本收录'
        '（繁体，非四库系底本）；词已另收《东坡词》，本集不重出。"\n---\n\n'
        '收录《东坡全集》一百十五卷，一卷一目录、一篇一文件。\n')
    print('写出 %d 卷 / %d 篇 / %d 汉字 (%.2f 万)' % (len(byvol), nfile, nchar, nchar / 10000))


if __name__ == '__main__':
    main()
