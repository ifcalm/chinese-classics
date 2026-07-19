#!/usr/bin/env python3
"""内容保真校验：把「仅补标点未改一字」这条铁律固化成可复跑的检查。

此前这套判据只活在会话级 scratchpad 里(punct-check<N>.py，清过一次)，
每卷都要临时重写；断句稿与 base-data 一旦脱节没有任何东西会报警——
2026-07-16 卷十二卷末题名即因此在 base-data / 断句稿 / 线上三处不一致。

用法:
    python3 scripts/check-integrity.py              # 全部检查，异常则非零退出
    python3 scripts/check-integrity.py --baseline   # 重建汉字流基线(改字后须人工复核再提交)
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANMING = os.path.join(ROOT, 'base-data/shushu/mingli/san-ming-tong-hui')
SCRIPTS = os.path.join(ROOT, 'scripts')
BASELINE = os.path.join(SCRIPTS, 'sanming-hanzi-baseline.json')

# 与断句时同一套判据：剥标点/空白后剩下的即「字」，此流永不得变
STRIP = set('，。；：、（）「」『』《》？！　 \n\t—─·…#"')

FM = re.compile(r'\A---\n.*?\n---\n', re.S)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def body_of(text):
    """剥 markdown frontmatter，返回正文。"""
    m = FM.match(text)
    return text[m.end():] if m else text


def hanzi(text):
    return ''.join(c for c in body_of(text) if c not in STRIP)


def vol_paths(k):
    return os.path.join(SANMING, '%03d.md' % k), os.path.join(SCRIPTS, 'sanming-c%d-punct.md' % k)


def check_draft_parity(errs):
    """断句稿与 base-data 正文须逐字一致。

    build_sanming 径读断句稿重建 base-data，两者脱节意味着「线上/构建产物」与
    「版本控制里的稿」讲的不是同一件事，重跑构建即静默改动正文。
    """
    for k in range(1, 13):
        bp, dp = vol_paths(k)
        b, d = body_of(read(bp)).strip(), read(dp).strip()
        if b == d:
            continue
        hb, hd = hanzi(read(bp)), read(dp)
        hd = ''.join(c for c in hd if c not in STRIP)
        detail = '汉字 base=%d 稿=%d 差%+d' % (len(hb), len(hd), len(hd) - len(hb))
        errs.append('卷%d 断句稿与 base-data 正文不一致(%s): %s vs %s'
                    % (k, detail, os.path.relpath(bp, ROOT), os.path.relpath(dp, ROOT)))


def check_punctuated(errs):
    """全书十二卷均已断句：base-data 若失去标点，说明被白文重排覆盖了。"""
    for k in range(1, 13):
        bp, _ = vol_paths(k)
        t = read(bp)
        if '，' not in t and '。' not in t:
            errs.append('卷%d base-data 无标点，疑被白文覆盖: %s' % (k, os.path.relpath(bp, ROOT)))


def hanzi_map():
    m = {}
    for k in range(1, 13):
        bp, _ = vol_paths(k)
        h = hanzi(read(bp))
        m['%03d' % k] = {'n': len(h), 'sha256': hashlib.sha256(h.encode()).hexdigest()}
    return m


def check_baseline(errs):
    """汉字流冻结基线：断句只补标点，故此流应永远不变；变了即是改字。"""
    if not os.path.exists(BASELINE):
        errs.append('缺基线文件，请先跑 --baseline 生成: %s' % os.path.relpath(BASELINE, ROOT))
        return
    want = json.loads(read(BASELINE))['volumes']
    got = hanzi_map()
    for k in sorted(want):
        if k not in got:
            errs.append('基线有卷%s，base-data 却没有' % k)
        elif got[k]['sha256'] != want[k]['sha256']:
            dn = got[k]['n'] - want[k]['n']
            how = '字数 %d→%d(%+d)' % (want[k]['n'], got[k]['n'], dn) if dn else '字数未变但字有替换'
            errs.append('卷%s 汉字流已变(%s)：断句不得改字，请复核是否手误' % (k, how))


BASE_DATA = os.path.join(ROOT, 'base-data')
QUOTES = os.path.join(ROOT, 'data/quotes.json')
CJK = re.compile(r'[㐀-鿿豈-﫿]')


def chapter_map():
    """chapterId → base-data md 路径。规则与 build-content.mjs 一致：
    相对路径去 .md、折叠数字分批目录段(\\d+-\\d+)、排除 _index.md。"""
    m = {}
    for dp, dns, fns in os.walk(BASE_DATA):
        dns[:] = [d for d in dns if not d.startswith('.')]
        for fn in fns:
            if not fn.endswith('.md') or fn == '_index.md':
                continue
            rel = os.path.relpath(os.path.join(dp, fn), BASE_DATA)[:-3]
            parts = [p for p in rel.split(os.sep) if not re.fullmatch(r'\d+-\d+', p)]
            m['/'.join(parts)] = os.path.join(dp, fn)
    return m


def check_quotes(errs):
    """名句库保真：data/quotes.json 每条名句的汉字流（剥标点空白后）须原样
    命中其 chapterId 指向的 base-data 篇章正文——名句永远不得与正文脱节，
    正文改字也会立即在此暴露。标点允许编辑（与断句同理），字不允许。"""
    if not os.path.exists(QUOTES):
        return 0
    quotes = json.loads(read(QUOTES)).get('quotes', [])
    cmap = chapter_map()
    body_cache = {}
    seen = set()
    for q in quotes:
        qid = q.get('id', '?')
        if qid in seen:
            errs.append('名句 id 重复: %s' % qid)
            continue
        seen.add(qid)
        missing = [f for f in ('text', 'source', 'chapterId') if not q.get(f)]
        if missing:
            errs.append('名句 %s 缺字段: %s' % (qid, ','.join(missing)))
            continue
        path = cmap.get(q['chapterId'])
        if not path:
            errs.append('名句 %s 的 chapterId 无对应篇章: %s' % (qid, q['chapterId']))
            continue
        flow = ''.join(CJK.findall(q['text']))
        if not flow:
            errs.append('名句 %s 无汉字' % qid)
            continue
        if path not in body_cache:
            body_cache[path] = ''.join(CJK.findall(body_of(read(path))))
        if flow not in body_cache[path]:
            errs.append('名句 %s 汉字流未命中出处 %s（逐字比对失败，勿凭记忆改句）'
                        % (qid, q['chapterId']))
    return len(quotes)


def main():
    if '--baseline' in sys.argv:
        total = sum(v['n'] for v in hanzi_map().values())
        with open(BASELINE, 'w', encoding='utf-8') as f:
            json.dump({
                '_': '三命通会汉字流基线：剥标点空白后的字流 sha256。断句仅补标点，故此流恒定；'
                     'CI 比对以防改字。改动前请确认是校勘决定而非手误。',
                'total': total,
                'volumes': hanzi_map(),
            }, f, ensure_ascii=False, indent=2)
        print('已写基线 %s（十二卷合计 %d 字）' % (os.path.relpath(BASELINE, ROOT), total))
        return 0

    errs = []
    check_draft_parity(errs)
    check_punctuated(errs)
    check_baseline(errs)
    n_quotes = check_quotes(errs)

    if errs:
        print('内容保真校验未通过：')
        for e in errs:
            print('  ✗ ' + e)
        return 1
    total = sum(v['n'] for v in hanzi_map().values())
    print('内容保真校验通过：三命通会十二卷 断句稿↔base-data 一致、均有标点、汉字流合基线（合计 %d 字）；'
          '名句库 %d 条逐字命中出处' % (total, n_quotes))
    return 0


if __name__ == '__main__':
    sys.exit(main())
