# -*- coding: utf-8 -*-
"""子部諸子九部·抓取。每部的頁面集在 BOOKS 裡寫死，抓什麼一目了然。"""
import subprocess, json, time, os

UA = 'chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API = 'https://zh.wikisource.org/w/api.php'
S = os.environ.get('ZZ_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(S, 'zzcache.json')

BOOKS = {
    '春秋繁露': ['春秋繁露'] + ['春秋繁露/卷%02d' % i for i in range(1, 18)],
    # 四部叢刊本用 <pages index=...djvu/> 轉錄掃描頁，wikitext 裡沒有正文；
    # 另有 白虎通/卷01-10 整理本（有標點），取之
    '白虎通': ['白虎通'] + ['白虎通/卷%02d' % i for i in range(1, 11)],
    # 新序/01-10 全是重定向，真實頁在 雜事/善謀 等分支下
    '新序': ['新序', '新序目錄序'] +
          ['新序/雜事/卷' + c for c in ['一', '二', '三', '亖', '五']] +
          ['新序/刺奢', '新序/節士', '新序/義勇',
           '新序/善謀/卷上', '新序/善謀/卷下'],
    '潛夫論': ['潛夫論'] + ['潛夫論/卷' + c for c in
             ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']] +
            ['潛夫論/附錄' + c for c in ['一', '二', '三', '四']],
    '申鑒': ['申鑒'] + ['申鑒/%d' % i for i in range(1, 6)] +
           ['申鑒/何孟春序', '申鑒/注申鑒序', '申鑒/王鏊序', '申鑒/跋申鑒注後'],
    '中論': ['中論 (儒家)', '中論 (儒家)/序', '中論 (儒家)/曾鞏序',
           '中論 (儒家)/刻徐幹中論序', '中論 (儒家)/卷之上', '中論 (儒家)/卷之下',
           '中論 (儒家)/中論後', '中論 (儒家)/後記'],
    '人物志': ['人物志', '人物志/自序'] +
            ['人物志/' + c for c in ['九徵', '體別', '流業', '材理', '材能', '利害',
                                    '接識', '英雄', '八觀', '七繆', '效難', '釋爭']],
    '劉子': ['劉子'] + ['劉子/%02d' % i for i in range(1, 31)],
    '長短經': ['長短經'] + ['長短經/卷' + c for c in
             ['一', '二', '三', '四', '五', '六', '七', '八', '九']],
}


def q(params):
    cmd = ['curl', '-4', '-s', '--max-time', '120', '-H', 'User-Agent: ' + UA, API]
    for k, v in params.items():
        cmd += ['--data-urlencode', '%s=%s' % (k, v)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(1.4)
    return json.loads(r.stdout)


def main():
    pages = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    titles = [t for v in BOOKS.values() for t in v]
    todo = [t for t in titles if t not in pages]
    print('待抓 %d/%d' % (len(todo), len(titles)))
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
        print('  已抓 %d' % len(pages))
    if miss: print('⚠ 缺页:', miss)
    print('完成，共 %d 页' % len(pages))


if __name__ == '__main__':
    main()
