#!/usr/bin/env python3
"""渲染 HTML → 站内纯文本。诗行一句一段（同李太白集/王临川集体例）。"""
import html, json, re

# 未登记的标记一律硬失败，不静默放行
KNOWN = {'p','br','div','span','small','a','u','h2','h3','h4','b','i','s','sup','sub',
         'dl','dd','dt','table','tbody','tr','td','th','link','style','meta','pre',
         'hr','blockquote','ol','ul','li','cite','abbr','dfn','big','strong','em','tt',
         'center','font','poem','section','figure','figcaption','img','ruby','rt','rp',
         'code','references','ref','q','var','samp','kbd','mark','del','ins'}


def detag(t):
    # ① variant-tooltip 必须整块先删，否则「一作X」漏进正文（王临川集教训）
    t = re.sub(r'<span class="variant-tooltip">.*?</span>', '', t, flags=re.S)
    # ② 编辑链接、样式、脚注引用
    t = re.sub(r'<span class="mw-editsection">.*?</span>', '', t, flags=re.S)
    t = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', t, flags=re.S)
    t = re.sub(r'<sup[^>]*class="[^"]*reference[^"]*"[^>]*>.*?</sup>', '', t, flags=re.S)
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    # 拼批渲染时 <ref group> 的报错块会落到相邻篇，整块删（源本无此内容）
    t = re.sub(r'<span class="error[^"]*"[^>]*>.*?</span>', '', t, flags=re.S)
    t = re.sub(r'<[^>]*class="mw-references[^"]*"[^>]*>.*?</[a-z]+>', '', t, flags=re.S)
    # ③ {{*}} 夹注：内容自带（），仅去 font-size:0 的隐形〈〉标记
    t = re.sub(r'<span style="color:transparent;font-size:0px">[〈〉]</span>', '', t)
    # ④ 结构 → 换行
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'</(p|div|dd|dt|li|tr|blockquote)>', '\n\n', t)
    for lv in (2, 3, 4):
        t = re.sub(r'<h%d[^>]*>(.*?)</h%d>' % (lv, lv),
                   lambda m: '\n\n### %s\n\n' % re.sub(r'<[^>]+>', '', m.group(1)).strip(),
                   t, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = t.replace('‎', '').replace('​', '')
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def blocks(t):
    """诗行/散段统一成「空行分段」。"""
    out = []
    for para in re.split(r'\n{2,}', t):
        para = para.strip()
        if not para:
            continue
        if para.startswith('###'):
            out.append(para)
            continue
        for line in para.split('\n'):
            line = line.strip()
            if line:
                out.append(line)
    return out


def main():
    h = json.load(open('dp-html3.json', encoding='utf-8'))
    items = json.load(open('dp-build.json', encoding='utf-8'))['items']
    bad = set()
    for x in h:
        for m in re.finditer(r'<(\w[\w-]*)', x):
            if m.group(1).lower() not in KNOWN:
                bad.add(m.group(1))
    if bad:
        raise SystemExit('!! 未登记标签: %s' % sorted(bad))
    out = []
    empty = []
    for x, raw in zip(items, h):
        b = blocks(detag(raw))
        if not b:
            empty.append((x['vol'], x['display']))
        out.append(b)
    print('转文本 %d 篇' % len(out))
    if empty:
        print('!! 空正文 %d 篇: %s' % (len(empty), empty[:20]))
    json.dump(out, open('dp-text2.json', 'w', encoding='utf-8'), ensure_ascii=False)
    i = [k for k, x in enumerate(items) if x['display'] == '赤壁賦'][0]
    print('\n=== 赤壁賦（前6段）'); print('\n\n'.join(out[i][:6]))
    j = [k for k, x in enumerate(items) if '獵會詩敘' in x['display']][0]
    print('\n=== 獵會詩敘（前3段）'); print('\n\n'.join(out[j][:3]))


if __name__ == '__main__':
    main()
