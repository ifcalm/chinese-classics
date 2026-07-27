#!/usr/bin/env python3
"""汇总《東坡全集》全部篇正文（wikitext），落 dp-corpus.json。

三条补源通道：主抓取 → 標題轉繁重試 → 東坡志林卷页分节。
无法解决的索引红链逐条挂账，不静默丢弃。
"""
import json, re, ws

# 索引红链，逐条判定（见 collation-log）
DROP = {
    '附錄': '卷115 索引红链，维基无此页',
    '又': '卷53/96/99 索引红链，通名无页',
    '再次前韻（系織錦圖上回文）': '卷29 红链；裸「再次前韻」是王安石诗(from=王臨川集)，非苏轼，不可代',
    '次韻參寥詠雪（此詩卷十八已收，時題為「次韻參寥同前」。）': '卷29 索引自注已收于卷18「次韻參寥同前」，同篇重出',
    '好事近（煙外倚危樓）': '卷115 词，本就在跳过之列；裸「好事近」是消歧义页',
}
FIX = {'爾朱道士煉硃砂丹': '爾朱道士煉朱砂丹', '汴河鬥門': '汴河斗門'}


def main():
    idx = json.load(open('wlc-idx.json', encoding='utf-8'))
    raw = json.load(open('dp-raw.json', encoding='utf-8'))
    zhilin = json.load(open('zhilin-sec.json', encoding='utf-8'))
    restmap = json.load(open('rest-map.json', encoding='utf-8'))
    text, redir = raw['text'], raw['redirect']

    # 转繁通道取回的 16 篇
    tr = sorted({v for k, v in restmap.items() if v != k})
    r = ws.post({'action': 'query', 'titles': '|'.join(tr + [FIX['爾朱道士煉硃砂丹']]),
                 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main',
                 'redirects': 1, 'format': 'json', 'formatversion': '2'}, 'rest23b')
    for p in r['query']['pages']:
        if 'missing' not in p:
            text[p['title']] = p['revisions'][0]['slots']['main']['content']

    def lookup(t):
        for k in (t, redir.get(t), restmap.get(t), FIX.get(t)):
            if k and k in text:
                return text[k], 'page'
        for k in (t, FIX.get(t)):
            if k and k in zhilin:
                return zhilin[k], 'zhilin'
        return None, None

    corpus, drops, unresolved = [], [], []
    seen = set()
    src = {'page': 0, 'zhilin': 0}
    for v in idx:
        for it in v['items']:
            t = it['target']
            if t in DROP:
                drops.append((v['vol'], t, DROP[t]))
                continue
            body, how = lookup(t)
            if body is None:
                unresolved.append((v['vol'], t))
                continue
            src[how] += 1
            key = (v['vol'], t)
            if key in seen:
                continue
            seen.add(key)
            corpus.append({'vol': v['vol'], 'target': t, 'display': it['display'],
                           'group': it['group'], 'src': how, 'wikitext': body})
    print('汇总 %d 条  (独立页 %d / 志林卷页分节 %d)' % (len(corpus), src['page'], src['zhilin']))
    print('挂账红链 %d 条:' % len(drops))
    for v, t, why in drops:
        print('   卷%-4d %-22s %s' % (v, t[:20], why))
    if unresolved:
        print('!! 未解决 %d 条: %s' % (len(unresolved), unresolved[:20]))
        raise SystemExit(1)
    json.dump(corpus, open('dp-corpus.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
