# -*- coding: utf-8 -*-
"""《廿二史札记》全本 ← 殆知阁本（简体）。

**为什么单开一支**：此前站内这部书出自维基文库，而维基条目本身只有 10,938 汉字
（小引＋卷一前十四条，约全书 2%），且页首挂今人导读、页尾挂外链节。全本维基没有，
ctext 的 API 需注册 IP 或密钥、robots.txt 亦禁 AI 抓取，故用户 2026-08-26 拍板改用
殆知阁本。**本书已从 `scripts/shibu/sb_build.py` 的 BOOKS 移出**，否则那边一跑就
拿维基残页把全本盖掉。

**底本**：garychowcmu/daizhigev20 之 `史藏/史评/廿二史札记.txt`，395,546 汉字，
简体、有句读。站内此书 variant 由繁转简，是换源不是转换——简→繁属改字，绝不可为。

**取舍**：钱大昕序、李保泰序系他人所撰，按铁律不收；赵翼自撰《小引》存。
首行「廿二史箚记 清 赵翼」是书名题署行，非正文。

**已知讹字**（见 docs/known-issues.md）：殆知阁本有一类系统性替换讹误，
「灵」作「炅」（149 处，「汉灵帝」全书作「炅帝」）、「未」作「吸」（36 处，
「未就」作「吸锻」）等，另有 157 处拆字残迹（「䌷」作「纟由」）与 6 处「■」。
**一律照收不改**——只删不改不增是铁律，系统性替换看似可逆，一改就是往正文写字。

用法: python3 scripts/parse-zhaji.py [--write]
"""
import os, re, sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dzg', '廿二史札记.txt')
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'base-data/history/nian-er-shi-zha-ji')
WRITE = '--write' in sys.argv
HAN = re.compile(r'[一-鿿㐀-䶿]')
han = lambda s: len(HAN.findall(s))

# 他人序不收（铁律）。小引是赵翼自序，收。
DROP_SEC = ('序（一）', '序（二）')

SUMMARY = ('清赵翼撰，凡三十六卷，就正史纪、传、表、志参互勘校，兼论历代治乱兴衰之故，'
           '与钱大昕《廿二史考异》、王鸣盛《十七史商榷》并称清代三大史考。'
           '据殆知阁本收录（简体）；钱大昕、李保泰二序系他人所撰不收，赵翼自撰《小引》存。')


def fm(**kw):
    out = ['---']
    for k, v in kw.items():
        out.append('%s: %s' % (k, v if isinstance(v, (int, float)) else '"%s"' % v))
    return '\n'.join(out) + '\n---\n'


def parse():
    lines = open(SRC, encoding='utf-8').read().split('\n')[1:]   # 首行是书名题署
    secs, cur = [], None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith('●'):
            cur = {'title': s[1:].strip(), 'items': []}
            secs.append(cur)
        elif s.startswith('○'):
            if cur is None:
                continue
            cur['items'].append({'title': s[1:].strip(), 'body': []})
        elif cur is not None:
            if not cur['items']:      # 卷首无条目题的散文（小引即此）
                cur['items'].append({'title': cur['title'], 'body': []})
            cur['items'][-1]['body'].append(s)
    return [x for x in secs if x['title'] not in DROP_SEC]


def main():
    secs = parse()
    tot = npiece = 0
    for vi, sec in enumerate(secs, 1):
        for it in sec['items']:
            tot += han(''.join(it['body'])) + han(it['title'])
            npiece += 1
    print('卷 %d · 篇 %d · 汉字 %d' % (len(secs), npiece, tot))
    if not WRITE:
        print('(dry-run)')
        return
    # 全量重写：先清掉旧的维基残页产物，免得新旧并存
    for dp, dns, fns in os.walk(BASE, topdown=False):
        for f in fns:
            if f.endswith('.md'):
                os.remove(os.path.join(dp, f))
        if dp != BASE:
            os.rmdir(dp)
    os.makedirs(BASE, exist_ok=True)
    open(os.path.join(BASE, '_index.md'), 'w', encoding='utf-8').write(
        fm(title='廿二史札记', weight=370, kind='book', author='赵翼',
           dynasty='清', summary=SUMMARY))
    for vi, sec in enumerate(secs, 1):
        d = os.path.join(BASE, '%03d' % vi)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=sec['title'], weight=vi))
        for j, it in enumerate(sec['items'], 1):
            open(os.path.join(d, '%04d.md' % j), 'w', encoding='utf-8').write(
                fm(title=it['title'].replace('"', '”'), weight=j)
                + '\n' + '\n\n'.join(it['body']) + '\n')
    print('已写入 %s' % BASE)


if __name__ == '__main__':
    main()
