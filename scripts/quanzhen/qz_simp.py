# -*- coding: utf-8 -*-
"""繁→简：走维基 LanguageConverter（variant=zh-hans；zh-cn 会静默不转，勿用）。

站点铁律「标题一律简体」，正文保持底本繁体。逐条请求要几千次，故拼成大块一次
渲染再切回——分隔符取 CJK 用不到的记号，转换器不会动它。
"""
import json, os, re, subprocess, time

UA = 'chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API = 'https://zh.wikisource.org/w/api.php'
SEP = '\n@@@%d@@@\n'
CACHE = os.environ.get('QZ_SIMP_CACHE', 'qz-simp.json')


def _post(params):
    cmd = ['curl', '-4', '-s', '--max-time', '90', '-H', 'User-Agent: ' + UA, API]
    for k, v in params.items():
        cmd += ['--data-urlencode', '%s=%s' % (k, v)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(1.5)
    return json.loads(r.stdout)


def _render(chunk):
    d = _post({'action': 'parse', 'text': chunk, 'contentmodel': 'wikitext',
               'prop': 'text', 'variant': 'zh-hans', 'formatversion': '2',
               'format': 'json', 'disablelimitreport': '1'})
    html = d['parse']['text']
    html = re.sub(r'<[^>]+>', '', html)
    return html


def to_simp(titles):
    """titles: 去重后的繁体串列表 → {繁: 简}。结果落缓存，重跑不再请求网络。"""
    have = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    todo = [t for t in dict.fromkeys(titles) if t and t not in have]
    for i in range(0, len(todo), 220):
        batch = todo[i:i + 220]
        chunk = ''.join((SEP % j) + t for j, t in enumerate(batch)) + (SEP % len(batch))
        txt = _render(chunk)
        parts = re.split(r'@@@\d+@@@', txt)[1:]
        if len(parts) < len(batch):
            raise SystemExit('切分失配：预期 %d 段，得 %d 段' % (len(batch), len(parts)))
        for t, p in zip(batch, parts):
            s = p.strip()
            # 渲染会给章节链接补 [编辑]，剥去（云笈七签同款坑）
            s = re.sub(r'\[\s*(编辑|編輯)\s*\]', '', s).strip()
            have[t] = s or t
        json.dump(have, open(CACHE, 'w'), ensure_ascii=False, indent=0)
        print('  繁→简 %d/%d' % (min(i + 220, len(todo)), len(todo)))
    return have
