#!/usr/bin/env python3
"""《東坡全集》批量渲染：预剥事务性模板 → 服务端渲染解模板 → 纯文本。

不逐页调 action=parse（6445 次请求太慢），改把多篇 wikitext 拼一块
POST 给 action=parse&text=，模板由服务端一次解开。
"""
import html, json, os, re, subprocess, sys, time

UA = 'chinese-classics-collector/1.0 (https://github.com/ifcalm/chinese-classics; ifcalm.ok@gmail.com)'
CACHE = 'ws-cache'
SEP = '\n\n@@@DPSEP@@@\n\n'
_last = [0.0]

# 事务性模板：与正文无关，渲染前先剥，既减负载又免渲染出导航块
KILL_TPL = ['Header', 'header', 'Textquality', 'textquality', 'PD-old', 'footer', 'Reflist',
            'reflist', 'Uncategorized', 'wikipedia', 'further', 'clr', 'Disambig', 'disambig',
            '消歧義', 'Wide image', 'gap', 'doc', '北宋作品', '唐朝作品', '宋朝作品', '西漢作品',
            '東漢作品', '南北朝作品', 'DEFAULTSORT', 'Novel', 'Novel-f']


def strip_tpl(t, names):
    """按名剥模板，从内向外多轮，避免非贪婪吞掉中段。"""
    pat = re.compile(r'\{\{\s*(?:%s)\s*(?:\|[^{}]*)?\}\}' % '|'.join(map(re.escape, names)))
    while True:
        n = pat.sub('', t)
        if n == t:
            return t
        t = n


def pre(t):
    t = re.sub(r'<ref[^>]*/>', '', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'<templatestyles[^>]*/?>', '', t)
    t = re.sub(r'\[\[(?:Category|分類|分类)\s*:[^\]]*\]\]', '', t, flags=re.I)
    t = re.sub(r'__[A-Z]+__', '', t)
    m = re.search(r'<onlyinclude>(.*?)</onlyinclude>', t, re.S)
    if m:
        t = m.group(1)
    # 尾部注释节（源用 ==註釋==/==注釋==/==參考==）
    t = re.split(r'\n\s*=+\s*(?:註釋|注釋|注释|參考|参考|校記|校记)\s*=+', t)[0]
    t = strip_tpl(t, KILL_TPL)
    # PUA 是维基自标的「无法识别的私用区字符」，按站内想尔注例存阙
    t = re.sub(r'\{\{\s*PUA\s*\|?[^{}]*\}\}', '□', t)
    return t.strip()


def post(params, key):
    p = os.path.join(CACHE, key + '.json')
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    gap = time.time() - _last[0]
    if gap < 1.5:
        time.sleep(1.5 - gap)
    cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA]
    for k, v in params.items():
        cmd += ['--data-urlencode', '%s=%s' % (k, v)]
    cmd.append('https://zh.wikisource.org/w/api.php')
    for i in range(5):
        out = subprocess.run(cmd, capture_output=True, text=True)
        _last[0] = time.time()
        try:
            d = json.loads(out.stdout)
            break
        except Exception:
            sys.stderr.write('\nretry %d %s: %s\n' % (i, key, out.stdout[:100]))
            time.sleep(6 * (i + 1))
    else:
        raise SystemExit('render failed ' + key)
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return d


def main():
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    bodies = [pre(x['wikitext']) for x in items]
    out, buf, idxs, batch = [None] * len(bodies), [], [], 0
    size = 0

    def flush():
        nonlocal buf, idxs, size, batch
        if not buf:
            return
        d = post({'action': 'parse', 'text': SEP.join(buf), 'contentmodel': 'wikitext',
                  'prop': 'text', 'format': 'json', 'formatversion': '2',
                  'wrapoutputclass': ''}, 'dp-render3-%04d' % batch)
        parts = d['parse']['text'].split('@@@DPSEP@@@')
        if len(parts) != len(buf):
            raise SystemExit('!! 批 %d 分片数 %d ≠ %d' % (batch, len(parts), len(buf)))
        for i, p in zip(idxs, parts):
            out[i] = p
        buf, idxs, size = [], [], 0
        batch += 1
        sys.stderr.write('\r渲染 %d/%d' % (sum(x is not None for x in out), len(out)))

    for i, b in enumerate(bodies):
        if size + len(b) > 60000 and buf:
            flush()
        buf.append(b)
        idxs.append(i)
        size += len(b)
    flush()
    sys.stderr.write('\n')
    json.dump(out, open('dp-html3.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('渲染完成 %d 篇，%d 批' % (len(out), batch))


if __name__ == '__main__':
    main()
