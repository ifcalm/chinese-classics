# -*- coding: utf-8 -*-
"""《廿二史札记》零改字校验：落盘汉字流须是殆知阁底本汉字流的【子序列】。

两侧不同源——本脚本不 import parse-zhaji，径自从 txt 抽汉字流（连两篇他人序、
书名题署行一并留着，故为落盘流的超集）；落盘侧连 frontmatter 篇题一起取，
因为条目题（○司马迁作史年岁）在底本里就是正文的一部分。
两个据印本补回、在殆知阁录文中缺失的篇题单独查对，其正文仍参加子序列校验。

用法: python3 scripts/verify-zhaji.py
"""
import os, re, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(R, 'scripts/dzg/廿二史札记.txt')
BASE = os.path.join(R, 'base-data/history/nian-er-shi-zha-ji')
HAN = re.compile(r'[一-鿿㐀-䶿]')
FM = re.compile(r'^---\n([\s\S]*?)\n---\n?')
RESTORED_HEADINGS = {
    ('021', '0005.md'): '方镇兵出境即仰度支供馈',
    ('023', '0010.md'): '一军中有五帝',
}


def disk():
    out = []
    dirs = sorted(x for x in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, x)))
    for d in dirs:
        dd = os.path.join(BASE, d)
        for f in sorted(x for x in os.listdir(dd) if x.endswith('.md') and x != '_index.md'):
            t = open(os.path.join(dd, f), encoding='utf-8').read()
            m = FM.match(t)
            title = re.search(r'^title:\s*"(.*)"$', m.group(1), re.M) if m else None
            restored = RESTORED_HEADINGS.get((d, f))
            if restored:
                if not title or title.group(1) != restored:
                    raise ValueError(f'{d}/{f} 补回的篇题与校勘记录不一致')
            elif title:
                out.append(''.join(HAN.findall(title.group(1))))
            out.append(''.join(HAN.findall(t[m.end():] if m else t)))
    return ''.join(out)


def is_sub(small, big):
    it = iter(big)
    return all(c in it for c in small)


def main():
    src = ''.join(HAN.findall(open(SRC, encoding='utf-8').read()))
    dsk = disk()
    ok = is_sub(dsk, src)
    print('底本 %d 字 · 落盘参与比对 %d 字 · 差 %d（两篇他人序＋书名题署行）'
          % (len(src), len(dsk), len(src) - len(dsk)))
    print('子序列判定：%s' % ('✔ 通过——只删未改未增' if ok else '✘ 不通过，有改字或增字'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
