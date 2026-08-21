# -*- coding: utf-8 -*-
"""科技門類·抓取。維基文庫 → kjcache.json。

**子頁自動枚舉**：這批書的分卷命名極不統一（《天工開物》按篇名 158 頁、
《農政全書》作 /卷01、《王禎農書》作 /卷一、《武經總要》作 /前集/卷一），
寫死頁名既冗長又易漏，故用 allpages 前綴列舉；列舉結果一併存進緩存，
事後可查當時抓了哪些頁。
"""
import subprocess, json, time, os, sys

UA = 'chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API = 'https://zh.wikisource.org/w/api.php'
S = os.environ.get('KJ_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(S, 'kjcache.json')
IDX = os.path.join(S, 'kjindex.json')

# 頁名（維基文庫繁體正題）→ 站內書。單頁書子頁數為 0，抓正題即可。
TITLES = [
    # 算學
    '九章算術', '周髀算經', '孫子算經', '海島算經', '五曹算經',
    '緝古算經', '數術記遺', '五經算術',
    # 農政
    '齊民要術', '農政全書', '農桑輯要', '王禎農書', '農書', '氾勝之書', '四民月令',
    # 工藝
    '天工開物', '營造法式', '武經總要',
    # 《農政全書》卷04 用 {{:井田攷 (徐光啓)}} 轉錄，須一併抓來內嵌
    '井田攷 (徐光啓)',
    # 譜錄
    '茶經', '茶錄', '大觀茶論', '宣和北苑貢茶錄', '糖霜譜',
    '荔枝譜', '橘錄', '菌譜', '洛陽牡丹記 (歐陽修)', '禽經',
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
