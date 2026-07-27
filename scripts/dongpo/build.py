#!/usr/bin/env python3
"""《東坡全集》定稿语料：逐类剔除污染，每一条剔除都留账。"""
import json, re, ws
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
SIMP = set('说门问钱国学时对为无与东车马长风开关这来个从们儿电点丽龙凤书画习节亲义华录汉觉')

# ① 维基该标题页实为他人作品（同题撞页），逐篇实测 author= 得出
WRONG_AUTHOR = {
    ('橄欖', 13): '王禹偁', ('郭綸', 26): '蘇轍', ('萬山', 27): '蘇洵', ('出峽', 27): '胡皓',
    ('槐', 27): '李嶠', ('贈人', 28): '李羣玉', ('李', 30): '李嶠', ('梨', 30): '李嶠',
    ('櫻桃', 30): '謝希孟', ('石榴', 30): '李商隱', ('槐', 30): '李嶠',
    ('酬劉柴桑', 31): '陶淵明', ('形贈影', 31): '陶淵明', ('影答形', 31): '陶淵明',
    ('神釋', 31): '陶淵明', ('怨詩楚調示龐主簿鄧治中', 31): '陶淵明', ('九日閑居', 31): '陶淵明',
    ('和胡西曹示顧賊曹', 31): '陶淵明', ('和劉柴桑', 32): '陶淵明',
    ('醉鄉記', 38): '王績', ('易論', 41): '蘇洵', ('詩論', 41): '蘇洵', ('禮論', 41): '蘇洵',
    ('春秋論', 41): '蘇洵', ('魏武帝論', 42): '朱敬則', ('賀正啟', 71): '黃滔',
    ('八陣圖', 102): '杜甫', ('記異', 103): '白居易', ('祭古冢文', 115): '謝惠連',
    ('論書', 115): '亞棲', ('水調歌頭', 115): '蘇轍',
}
# ② 维基页非《東坡全集》所出，系编者据他集补入
FOREIGN = {'追和陶淵明詩引（子由作。此引因對理解和陶詩大有幫助，故保留）': '蘇轍《潁濱文鈔》18',
           '古風（此秦觀詩）': '秦觀《淮海集》卷六，原題《精思》'}
# ③ 源页只有「此詩卷N已收」互见说明，正文为空
XREF = 6
# ④ 消歧义漏网
DISAMB2 = {'留侯論': '留侯論 (蘇軾)'}
# ⑤ 卷104 裴頠對武帝 独立页是简体录文，志林卷四同篇为繁体，取志林
PREFER_ZHILIN = {'裴頠對武帝'}


def main():
    d = json.load(open('dp-final.json', encoding='utf-8'))
    items = d['items']
    sec = json.load(open('zhilin-sec.json', encoding='utf-8'))
    r = ws.post({'action': 'query', 'titles': '|'.join(DISAMB2.values()), 'prop': 'revisions',
                 'rvprop': 'content', 'rvslots': 'main', 'redirects': 1,
                 'format': 'json', 'formatversion': '2'}, 'disamb2')
    extra = {p['title']: p['revisions'][0]['slots']['main']['content']
             for p in r['query']['pages'] if 'missing' not in p}

    out, log = [], {'wrong_author': [], 'foreign': [], 'xref': [], 'empty': [], 'simp': []}
    for x in items:
        base = re.split(r'\{\{', x['display'])[0].strip()
        key = (base, x['vol'])
        if key in WRONG_AUTHOR:
            log['wrong_author'].append([x['vol'], base, WRONG_AUTHOR[key]])
            continue
        if x['target'] in FOREIGN:
            log['foreign'].append([x['vol'], x['display'], FOREIGN[x['target']]])
            continue
        if x['target'] in PREFER_ZHILIN:
            x = dict(x, wikitext=sec[x['target']], src='zhilin',
                     note='独立页为简体录文，取《東坡志林》卷四繁体同篇')
        if x['target'] in DISAMB2:
            x = dict(x, wikitext=extra[DISAMB2[x['target']]], target=DISAMB2[x['target']],
                     note='消歧义归并')
        # 简体判定须先剥 <ref>：现代注释是简体，但本站本就不收注释
        clean = re.sub(r'<ref[^>]*>.*?</ref>', '', x['wikitext'], flags=re.S)
        clean = re.sub(r'\{\{[Hh]eader.*?\}\}', '', clean, flags=re.S)
        hz = HZ.findall(clean)
        hz = [ch for ch in hz if ch not in set('北宋作品唐朝西漢東漢南朝')]
        if '已收' in x['display'] and len(hz) < 12:
            log['xref'].append([x['vol'], x['display']])
            continue
        if not hz:
            log['empty'].append([x['vol'], x['display']])
            continue
        if len(hz) > 20 and sum(1 for c in hz if c in SIMP) / len(hz) > 0.02:
            log['simp'].append([x['vol'], x['display'], len(hz)])
            continue
        out.append(x)

    n = sum(len(HZ.findall(x['wikitext'])) for x in out)
    print('定稿 %d 篇 / wikitext 汉字 %d' % (len(out), n))
    for k, name in [('wrong_author', '同题撞页(他人作品)'), ('foreign', '非全集所出'),
                    ('xref', '互见空页'), ('empty', '源页空'), ('simp', '简体录文')]:
        print('  剔除 %-14s %d 条' % (name, len(log[k])))
    json.dump({'items': out, 'log': log, 'skipped_ci': d['skipped_ci'],
               'no_page': d['missing']}, open('dp-build.json', 'w', encoding='utf-8'),
              ensure_ascii=False)


if __name__ == '__main__':
    main()
