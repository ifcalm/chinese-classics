# -*- coding: utf-8 -*-
"""史部三通與史論·抓取。維基文庫 → sbcache.json。

子頁用 allpages 前綴自動枚舉，列舉結果存 sbindex.json。清洗與解析復用
`scripts/keji/kj_clean.py`、`kj_parse.py`。

**《蕙風詞話》不抓**：況周頤（1859–1926）卒於民國，屬近現代，按收錄鐵律不收。
**《康熙字典》《字彙》《廣雅》《溫公續詩話》不抓**：前二者是字書條目（每頁近百字、
零標點），後二者維基本只剩殘頁（371 字／3 字）。

**《讀通鑑論》維基文庫無此頁**；《大唐西域記》已在佛學/史傳部，不重收。

**2026-08-26 補目錄類**：《郡齋讀書志》20 子頁、《直齋書錄解題》22 子頁，皆全帙。
二書之「解題」是目錄提要，非注疏，不在「注疏不收」之列。
"""
import subprocess, json, time, os, sys

UA = 'chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API = 'https://zh.wikisource.org/w/api.php'
S = os.environ.get('SB_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(S, 'sbcache.json')
IDX = os.path.join(S, 'sbindex.json')

# 頁名（維基文庫繁體正題）→ 站內書。單頁書子頁數為 0，抓正題即可。
TITLES = [
    # 政書（三通、會要）
    '通典', '通志', '文獻通考', '唐會要',
    # 史論、史考
    '日知錄', '文史通義', '明夷待訪錄',   # 廿二史劄記改用殆知阁本，见 parse-zhaji.py
    # 雜史、傳記
    '東觀漢記', '大唐新語', '朝野僉載', '唐才子傳',
    # 目錄（2026-08-26 補：史部「目錄」一類此前為零）
    '郡齋讀書志', '直齋書錄解題',
    # 語錄、兵書（入子部）
    '朱子語類', '武經總要',
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
