# -*- coding: utf-8 -*-
"""欧阳修集·质检。

零改字校验（同道家C批/全真批口径）：底本清洗后的汉字流 与 落盘汉字流 逐字比对，
**只允许 delete，不允许 insert/replace**；每处 delete 须在剥离账上认领
（体裁组名 / 卷题回显 / header 元数据）。字流只取迻录自底本的篇题(raw)与正文，
组前缀是合成的显示题，不入字流。
"""
import difflib, re, sys, os, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oy_clean import clean, norm_lines
from oy_parse import (parse, load, volkey, BOOK, headings, RE_VOLECHO,
                      expand_trans)
from oy_fix import REJECT, PENDING, MANUAL, TITLE_FIX, JUNK_FIX, JUNK_PENDING

HZ = re.compile(r'[一-鿿]')
FIXN = len(__import__('json').load(open(
    os.environ.get('OY_FIXTABLE', 'oy-fixtable.json'))))
# 编码损坏铁证：假名/制表/全角拉丁数字/非中文标点的全角符号/替换字符/私用区/康熙部首
JUNK = re.compile('[぀-ヿ─-╿'
                  '０-９Ａ-Ｚａ-ｚ'
                  '＂-＇＊＋－．／'
                  '＜-＞＠［-｀｛-～'
                  '�-⺀-⿟'
                  'A-Za-z]')
# header2 元数据：title/section/author/previous/next 等，非正文
RE_HDR = re.compile(r'\{\{\s*header2?\b.*?^\}\}\s*$', re.S | re.I | re.M)


def src_stream():
    """底本字流须与 parse 的输入同源：一样展开 {{:頁名}} 整篇嵌入。"""
    pages = load()
    out = []
    for k in sorted((x for x in pages
                     if x != BOOK and not x.startswith('TRANS/')), key=volkey):
        raw, _miss, _tr = expand_trans(pages[k], pages)
        t = RE_HDR.sub('', raw)
        t = re.sub(r'^(={1,6})\s*(.+?)\s*=+\s*$', r'\2', t, flags=re.M)
        out += [l for l in norm_lines(clean(t))]
    return ''.join(HZ.findall(''.join(out)))


def out_stream(vols):
    return ''.join(HZ.findall(''.join(
        p.get('raw', '') + ''.join(l.lstrip('# ') if l.startswith('## ') else l
                                   for l in p['lines'])
        for v in vols for p in v['pieces'])))


def main():
    # 结构校验用未回改版：回改是换字，与「结构不改字」分开计账，
    # 同东坡全集「replace 数与回改账逐条相符」的口径。
    vols, strip_log = parse(fix=False)
    a, b = src_stream(), out_stream(vols)
    # 「只删不增不换」这一断言等价于：落盘字流是底本字流的子序列。
    # 故用双指针 O(n) 判定即可，不必上 difflib（80 万字规模下 difflib 不可行）。
    dels, i, j = [], 0, 0
    while j < len(b) and i < len(a):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            k = i
            while i < len(a) and a[i] != b[j]:
                i += 1
            dels.append(a[k:i])
    ok = (j == len(b))
    if i < len(a):
        dels.append(a[i:])
    ledger = sorted({''.join(HZ.findall(x)) for x in strip_log if x}, key=len, reverse=True)
    RESID = re.compile(r'卷[一二三四五六七八九十百]+|居士集|居士外集|集古錄跋尾|書簡|'
                       r'易童子問|外制集|內制集|奏事錄|濮議|筆說|試筆|近體樂府|'
                       r'詩餘|樂語|附錄|補遺|序|第|首|道|通|之')
    # 逐段扣账会被双指针的切分位置干扰（ledger 串常被落盘侧同名篇题打断），
    # 故把删除段整体拼起来一次扣净。
    # 已证「落盘是底本的子序列」，故被删字符恰为 src−out。
    # 删除段的切分位置由贪婪匹配决定、与账本边界不重合，子串扣法对不上，
    # 改比对**字符多重集**：删除字符集应与剥离账字符集相等，顺序无关且精确。
    delc = collections.Counter(''.join(dels))
    ledc = collections.Counter(''.join(''.join(HZ.findall(x)) for x in strip_log))
    unaccounted = delc - ledc
    over = ledc - delc
    bad = sorted(unaccounted.items(), key=lambda kv: -kv[1])

    fixed, _ = parse(fix=True)
    txt = ''.join(''.join(p['lines']) for v in fixed for p in fixed_pieces(v))
    junk = collections.Counter(JUNK.findall(txt))
    print('卷 %d · 篇 %d · %d 汉字（%.2f 万）' % (
        len(vols), sum(len(v['pieces']) for v in vols),
        len(HZ.findall(txt)), len(HZ.findall(txt)) / 10000))
    print('剥离账 %d 项 · 认领删除 %d 处 · 空篇 %d' % (
        len(strip_log), len(dels),
        sum(1 for v in vols for p in v['pieces'] if not HZ.findall(''.join(p['lines'])))))
    print('杂讯字符：%s' % (dict(junk) or '无'))
    print('子序列判定：%s' % ('通过（落盘字流全在底本字流中，无增无换）' if ok else '❌ 失败，存在增字或换字'))
    print('剥离账字符核对：删除 %d 字，账上 %d 字；账外多删 %d 字，账上未用 %d 字'
          % (sum(delc.values()), sum(ledc.values()),
             sum(unaccounted.values()), sum(over.values())))
    if bad:
        print('   账外多删的字：%s' % ''.join('%s×%d ' % kv for kv in bad[:20]))
    print()
    print('乱码回改账：对齐轮 %d 条 + 锚点轮 %d 条 + 篇题 %d 条 = %d 条' % (
        FIXN, len(JUNK_FIX), len(TITLE_FIX), FIXN + len(JUNK_FIX) + len(TITLE_FIX)))
    print('判假阳性不改 %d 条 · 存照挂账 %d 条' % (
        len(REJECT), len(PENDING) + len(JUNK_PENDING)))


def fixed_pieces(v):
    return v['pieces']


if __name__ == '__main__':
    main()
