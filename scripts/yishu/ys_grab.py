# -*- coding: utf-8 -*-
"""藝術門類·抓取。維基文庫 → yscache.json。

子頁用 allpages 前綴自動枚舉，列舉結果存 ysindex.json，事後可查當時抓了哪些頁。
清洗與解析復用 `scripts/keji/kj_clean.py`、`kj_parse.py`——同是維基文庫整理本，
模板體例一致，另起一套只會分叉。
"""
import subprocess, json, time, os, sys

UA = 'chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API = 'https://zh.wikisource.org/w/api.php'
S = os.environ.get('YS_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(S, 'yscache.json')
IDX = os.path.join(S, 'ysindex.json')

# 頁名（維基文庫繁體正題）→ 站內書。單頁書子頁數為 0，抓正題即可。
TITLES = [
    # 畫論
    '古畫品錄', '續畫品', '敘畫', '歷代名畫記', '唐朝名畫錄', '筆法記',
    '益州名畫錄', '圖畫見聞誌', '林泉高致集', '山水純全集', '宣和畫譜', '畫繼',
    '畫禪室隨筆', '苦瓜和尚畫語錄',
    # 書論
    # 《書斷》的序不在 書斷/ 之下：書斷/序 是到 書斷序 的重定向
    '筆陣圖', '書譜', '書斷', '書斷序', '法書要錄', '宣和書譜', '衍極', '書法雅言', '藝舟雙楫',
    # 樂論
    '樂府古題要解', '教坊記', '羯鼓錄', '樂府雜錄', '琴史',
    # 器物
    '陶說', '景德鎮陶錄',
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
