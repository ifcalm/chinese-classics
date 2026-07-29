#!/usr/bin/env python3
"""零改字校验：产出汉字流 vs 源汉字流，只许 delete，逐条核对删了什么。"""
import difflib, json, re
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
RAW = json.load(open('c-raw.json', encoding='utf-8'))
P = json.load(open('c-parsed.json', encoding='utf-8'))
ORDER = {'性命圭旨': ['性命圭旨/元集', '性命圭旨/亨集', '性命圭旨/利集', '性命圭旨/貞集'],
         '淨明忠孝全書': ['淨明忠孝全書/序'] + ['淨明忠孝全書/%d' % i for i in range(1, 7)]}
ok = True
for book, d in P.items():
    keys = ORDER.get(book, sorted(RAW[book]))
    src = ''.join(HZ.findall('\n'.join(RAW[book][k] for k in keys)))
    body = '\n'.join('\n'.join(x['blocks']) for x in d['items'])
    # 〔…〕是站内校补/编者说明的既定标记，不属底本正文，比对前剔除
    body = re.sub(r'〔[^〕]*〕', '', body)
    got = ''.join(HZ.findall(body))
    dels, ins, rep = [], [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, got, autojunk=False).get_opcodes():
        if tag == 'delete':
            dels.append(src[i1:i2])
        elif tag == 'insert':
            ins.append(got[j1:j2])
        elif tag == 'replace':
            rep.append((src[i1:i2], got[j1:j2]))
    nd = sum(map(len, dels))
    print('══ %-24s 删 %4d  增 %3d  换 %3d %s'
          % (book, nd, sum(map(len, ins)), sum(len(a) for a, _ in rep),
             '✅' if not ins and not rep else '❌'))
    if ins or rep:
        ok = False
        print('   增:', ins[:6]); print('   换:', rep[:6])
    big = sorted(dels, key=len, reverse=True)[:6]
    print('   删除项(长→短):', [x[:40] for x in big])
print()
print('总判定:', '✅ 全部只删不增不换' if ok else '❌ 有增/换，须查')
