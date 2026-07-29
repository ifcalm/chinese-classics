#!/usr/bin/env python3
"""列出整理本 vs 四庫本的全部非异体差异，供人工裁定。"""
import difflib, json, re, unicodedata
import hj_collate as C
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
A = json.load(open('hj-raw.json', encoding='utf-8'))
W = json.load(open('hj-siku.json', encoding='utf-8'))


def variant_pair(x, y):
    """同长且逐字为『同一字的不同字形』——用 Unicode 兼容分解 + 常见刻本异体近似判定。"""
    if len(x) != len(y) or not x:
        return False
    for a, b in zip(x, y):
        if a == b:
            continue
        if C.NORM.get(a, a) == C.NORM.get(b, b):
            continue
        return False
    return True


rows = []
for ka, kw in C.PAIR:
    a = C.norm(''.join(HZ.findall(re.sub(r'\{\{[^{}]*\}\}|^==.*?==$', '', A[ka], flags=re.M))))
    b = C.norm(''.join(HZ.findall(C.strip_siku(W[kw]))))
    raw_a = ''.join(HZ.findall(re.sub(r'\{\{[^{}]*\}\}|^==.*?==$', '', A[ka], flags=re.M)))
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        x, y = raw_a[i1:i2], b[j1:j2]
        if variant_pair(a[i1:i2], y):
            continue
        rows.append((ka.split('/')[1], tag, x, y, raw_a[max(0, i1 - 11):i1], raw_a[i2:i2 + 11]))
print('非异体差异 %d 处：' % len(rows))
for v, tag, x, y, pre, post in rows:
    if len(x) > 24 or len(y) > 24:
        print('  %-4s [长块 %s] 整理本《%s》\n            四庫本《%s》' % (v, tag, x[:60], y[:60]))
    else:
        print('  %-4s 整理本《%-8s》← 四庫本《%-8s》  …%s〖%s〗%s…' % (v, x, y, pre, x, post))
json.dump(rows, open('hj-diff.json', 'w', encoding='utf-8'), ensure_ascii=False)
