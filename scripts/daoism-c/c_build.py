#!/usr/bin/env python3
"""道家 C 批八部：切篇 → 结构化中间件（未落盘，先过质检）。"""
import json, re
from c_parse import *

RAW = json.load(open('c-raw.json', encoding='utf-8'))


def abstract_of(t):
    m = ABSTRACT.search(t)
    return (m.group(0).strip(), ABSTRACT.sub('', t)) if m else ('', t)


def xingming():
    """性命圭旨：元亨利贞四集，33 说，篇题为「说」名，集名并入篇题前缀。"""
    out = []
    for ji in ['元集', '亨集', '利集', '貞集']:
        t = RAW['性命圭旨']['性命圭旨/' + ji]
        t = re.sub(r'^\s*%s\s*$' % ji, '', t, flags=re.M)
        for title, body in split_head(t, 3):
            b = paras(clean(body))
            if not b:
                continue
            out.append({'title': title or ji, 'ji': ji, 'blocks': b})
    return out, ''


def ganying():
    t = RAW['太上感應篇集註']['太上感應篇集註']
    out = []
    for title, body in split_head(t, 2):
        if not title:
            continue
        b = jing_zhu(body) if '{{*s}}' in body else paras(clean(body))
        if b:
            out.append({'title': title, 'blocks': b})
    return out, ''


def jingming():
    out = []
    order = ['序'] + [str(i) for i in range(1, 7)]
    for k in order:
        t = RAW['淨明忠孝全書']['淨明忠孝全書/' + k]
        secs = split_head(t, 2)
        vol = '卷之' + '一二三四五六'[int(k) - 1] if k != '序' else '序'
        for title, body in secs:
            b = paras(clean(body))
            if not b:
                continue
            out.append({'title': title or vol, 'vol': vol, 'blocks': b})
    return out, ''


def chishu():
    t = RAW['太上洞玄靈寶赤書玉訣妙經']['太上洞玄靈寶赤書玉訣妙經']
    summ, t = abstract_of(t)
    parts = re.split(r'^\s*(太上洞玄靈寶赤書玉訣妙經卷[上下])\s*$', clean(t), flags=re.M)
    out, i = [], 1
    while i + 1 < len(parts) + 1 and i < len(parts):
        title, body = parts[i], parts[i + 1] if i + 1 < len(parts) else ''
        b = [x for x in paras(body) if x != title]
        if b:
            # 源页首行与卷题同文，切出两段同名，合并（卷上重出）
            if out and out[-1]['title'] == title:
                out[-1]['blocks'] += b
            else:
                out.append({'title': title, 'blocks': b})
        i += 2
    return out, summ


def qinghua():
    t = RAW['玉清金笥青華秘文金寶內鍊丹訣']['玉清金笥青華秘文金寶內鍊丹訣']
    out = []
    for title, body in split_head(t, 2):
        b = paras(clean(body))
        if b:
            out.append({'title': title or '卷首', 'blocks': b})
    return out, ''


def miaomen():
    t = RAW['一切道經音義妙門由起']['一切道經音義妙門由起']
    summ, t = abstract_of(t)
    t = clean(t)
    i = t.find('妙門由起序')
    out = [{'title': '一切道经音义序', 'blocks': paras(t[:i])},
           {'title': '妙门由起', 'blocks': paras(t[i:])}]
    return [x for x in out if x['blocks']], summ


def gushen():
    t = RAW['谷神篇']['谷神篇']
    out = []
    for h2, body in split_head(t, 2):
        if not h2:
            continue
        subs = split_head(body, 3)
        if len(subs) == 1 and subs[0][0] is None:
            b = paras(clean(body))
            if b:
                out.append({'title': h2, 'blocks': b})
            continue
        for h3, sb in subs:
            b = paras(clean(sb))
            if not b:
                b = ['〔原書有圖，底本闕〕']
            out.append({'title': h3 or h2, 'vol': h2, 'blocks': b})
    return out, ''


def yixian():
    t = RAW['疑仙傳']['疑仙傳']
    out = []
    for title, body in split_head(t, 2):
        if not title:
            continue
        b = paras(clean(body))
        if b:
            out.append({'title': title, 'blocks': b})
    return out, ''


BOOKS = [('性命圭旨', xingming), ('太上感應篇集註', ganying), ('淨明忠孝全書', jingming),
         ('太上洞玄靈寶赤書玉訣妙經', chishu), ('玉清金笥青華秘文金寶內鍊丹訣', qinghua),
         ('一切道經音義妙門由起', miaomen), ('谷神篇', gushen), ('疑仙傳', yixian)]

res = {}
for name, fn in BOOKS:
    check_templates('\n'.join(RAW[name].values()), name)
    items, summ = fn()
    n = sum(len(HZ.findall('\n'.join(x['blocks']))) for x in items)
    src = len(HZ.findall(''.join(RAW[name].values())))
    print('%-24s %2d 篇 %7d 字（源 %d，留存 %.1f%%）%s'
          % (name, len(items), n, src, n / src * 100, ('｜提要 ' + summ[:26]) if summ else ''))
    empty = [x['title'] for x in items if not ''.join(x['blocks']).strip()]
    if empty:
        print('   !! 空篇: %s' % empty)
    res[name] = {'items': items, 'summary': summ}
json.dump(res, open('c-parsed.json', 'w', encoding='utf-8'), ensure_ascii=False)
