# -*- coding: utf-8 -*-
"""小學與詩文評·抓取。維基文庫 → xxcache.json。

子頁用 allpages 前綴自動枚舉，列舉結果存 xxindex.json。清洗與解析復用
`scripts/keji/kj_clean.py`、`kj_parse.py`。

**《蕙風詞話》不抓**：況周頤（1859–1926）卒於民國，屬近現代，按收錄鐵律不收。
**《康熙字典》《字彙》《廣雅》《溫公續詩話》不抓**：前二者是字書條目（每頁近百字、
零標點），後二者維基本只剩殘頁（371 字／3 字）。
"""
import subprocess, json, time, os, sys

UA = 'chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API = 'https://zh.wikisource.org/w/api.php'
S = os.environ.get('XX_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(S, 'xxcache.json')
IDX = os.path.join(S, 'xxindex.json')

# 頁名（維基文庫繁體正題）→ 站內書。單頁書子頁數為 0，抓正題即可。
TITLES = [
    # 小學（訓詁、韻書）
    '方言', '釋名', '急就篇', '廣韻', '中原音韻',
    # 詩文評
    '詩品', '二十四詩品', '六一詩話', '中山詩話', '滄浪詩話', '歲寒堂詩話',
    '白石道人詩說', '碧雞漫志', '樂府指迷', '四溟詩話', '薑齋詩話', '原詩',
    '說詩晬語', '隨園詩話', '詞概',
]


def q(params):
    cmd = ['curl', '-4', '-s', '--max-time', '120', '-H', 'User-Agent: ' + UA, API]
    for k, v in params.items():
        cmd += ['--data-urlencode', '%s=%s' % (k, v)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(1.2)
    return json.loads(r.stdout)


def subpages(prefix):
    out, cont = [], {}
    while True:
        d = q(dict({'action': 'query', 'list': 'allpages', 'apprefix': prefix + '/',
                    'apnamespace': '0', 'aplimit': '500', 'format': 'json',
                    'formatversion': '2'}, **cont))
        out += [p['title'] for p in d['query']['allpages']]
        if 'continue' not in d:
            return sorted(out)
        cont = d['continue']


def main():
    pages = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    index = json.load(open(IDX, encoding='utf-8')) if os.path.exists(IDX) else {}
    for t in TITLES:
        if t not in index:
            index[t] = [t] + subpages(t)
            json.dump(index, open(IDX, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            print('%-22s 子页 %d' % (t, len(index[t]) - 1))
    todo = [x for v in index.values() for x in v if x not in pages]
    print('待抓 %d 页' % len(todo))
    miss = []
    for i in range(0, len(todo), 20):
        d = q({'action': 'query', 'prop': 'revisions', 'rvprop': 'content',
               'rvslots': 'main', 'titles': '|'.join(todo[i:i + 20]),
               'format': 'json', 'formatversion': '2'})
        for p in d['query']['pages']:
            if p.get('missing'):
                miss.append(p['title']); continue
            pages[p['title']] = p['revisions'][0]['slots']['main']['content']
        json.dump(pages, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
        sys.stdout.write('\r  %d/%d' % (min(i + 20, len(todo)), len(todo))); sys.stdout.flush()
    print('\n缓存 %d 页；缺页 %d %s' % (len(pages), len(miss), miss[:6]))


if __name__ == '__main__':
    main()
