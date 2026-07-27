#!/usr/bin/env python3
"""非汉字杂讯字符逐处取四庫本对读（假名/制表符/全角拉丁/U+FFFD 均系编码损坏铁证）。"""
import glob, json, os, re
import wlc_sweep as W
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
FM = re.compile(r'\A---\n.*?\n---\n', re.S)
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/wang-lin-chuan-ji'
JUNK = re.compile('[' + re.escape('ㄧㄖぃきゼダヨ┕┤Ｏ＃ufffdue18c⑽') + ']')

siku = {int(k): W.norm(v) for k, v in json.load(open('wlc-siku.json', encoding='utf-8')).items()}
for p in sorted(glob.glob(BASE + '/*/*.md')):
    if p.endswith('_index.md'):
        continue
    t = open(p, encoding='utf-8').read()
    m = FM.match(t)
    b = t[m.end():]
    if not JUNK.search(b):
        continue
    vol = int(os.path.basename(os.path.dirname(p)))
    hay = siku.get(vol, '')
    for mm in JUNK.finditer(b):
        i = mm.start()
        pre = ''.join(HZ.findall(b[max(0, i - 40):i]))[-8:]
        post = ''.join(HZ.findall(b[i + 1:i + 60]))[:8]
        j = hay.find(W.norm(pre))
        got = hay[j + len(pre): j + len(pre) + 14] if j >= 0 else '(锚不上)'
        print('%-12s %r' % (os.path.relpath(p, BASE), mm.group(0)))
        print('    整理本 …%s〖%s〗%s…' % (pre, mm.group(0), post))
        print('    四庫本 …%s〖%s〗…' % (pre, got))
