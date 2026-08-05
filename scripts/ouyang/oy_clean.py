# -*- coding: utf-8 -*-
"""欧阳修集·底本清洗。

底本：维基文库《歐陽修集》153 卷 + 補遺 + 附錄五种（繁体，有新式标点）。
底本鉴别：玄 65 / 弘 18 / 匡 1 / 胤 7 皆不避讳，「臣等謹案」0 处——**非四库系**，
是 source-risk-audit(#34) 要的可追溯专书本。简体指纹 0.01‰。
"""
import re

# ── 缺字：源以 svg 图给出真字（alt 即字），同王临川集「缺字存形借证人得真字」例 ──
RE_FILE_CHAR = re.compile(r'\[\[File:[^\]|]*\.svg\|[^\]|]*\|([^\]|]+)\]\]', re.I)
# ── 铭文拓片为图片，只存图题，同性命圭旨「剥图留题」例 ──
RE_FILE_IMG = re.compile(r'\[\[File:[^\]|]*\.(?:png|jpg|jpeg|gif)\|[^\]|]*\|([^\]|]+)\]\]', re.I)

UNKNOWN = set()          # 清洗中遇到的未登记模板名，供质检核对
DROP_TMPL = ('Textquality', 'header2', 'header', 'Header', 'PD-old', 'PD-China',
             '宋朝作品', '北宋作品', 'Col-begin', 'Col-break', 'Col-end',
             'album header', '檢索', 'edition', 'footer', '署名', '明朝作品')


def _tmpl(t):
    """模板逐层由内向外解：夹注转括注、年号留字面、缺字取真字、异文留主字。"""
    for _ in range(6):
        before = t
        t = re.sub(r'\{\{\s*YL\s*\|([^{}|]*)\}\}', r'\1', t)              # 年号留字面
        t = re.sub(r'\{\{\s*!\s*\|([^{}|]*)\|[^{}]*\}\}', r'\1', t)        # 缺字存形，取首参
        t = re.sub(r'\{\{\s*另\d?\s*\|([^{}|]*)\|[^{}]*\}\}', r'\1', t)      # 异文留主字（另/另2）
        t = re.sub(r'\{\{\s*~\s*\|([^{}]*)\}\}', r'\1', t)                  # 评语框，去框留文
        # 维基自标「私用区编码无法识别」，无从查实不猜字，作 □ 存阙（同东坡全集例）
        t = re.sub(r'\{\{\s*PUA\s*\|[^{}]*\}\}', '□', t)
        t = re.sub(r'\{\{\s*\?\s*\}\}', '□', t)                              # 源自标缺字
        # 夹注转括注；内容自带全角括号者不再重复包裹（同徐霞客〔…〕教训）
        t = re.sub(r'\{\{\s*[*\-]\s*\|([^{}]*)\}\}',
                   lambda m: m.group(1).strip() if re.fullmatch(r'（.*）', m.group(1).strip())
                   else '（%s）' % m.group(1).strip(), t)
        t = re.sub(r'\{\{\s*(?:%s)\b[^{}]*\}\}' % '|'.join(DROP_TMPL), '', t, flags=re.I | re.S)
        if t == before:
            break
    # ⚠ catch-all 绝不能连内容一起删：附錄四 35 篇评语正文一度就是这样整块消失的
    # （模板内无 -{…}- 者被此条吞掉，且因 src_stream 同样调用 clean 而对零改字校验隐形）。
    # 故未知模板一律留其内容，并登记备查。
    def _keep(m):
        inner = m.group(0)[2:-2]
        name = inner.split('|', 1)[0].strip()
        if name in DROP_TMPL:
            return ''
        UNKNOWN.add(name)
        return inner.split('|', 1)[1] if '|' in inner else ''
    t = re.sub(r'\{\{[^{}]*\}\}', _keep, t)
    return t


def clean(t):
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'<ref[^>]*/>', '', t)
    t = RE_FILE_CHAR.sub(lambda m: m.group(1), t)
    t = RE_FILE_IMG.sub(lambda m: '〔圖：%s〕' % m.group(1), t)
    t = re.sub(r'\[\[File:[^\]]*\]\]', '', t, flags=re.I)
    for _ in range(3):                        # 字词转换标记先解：其花括号会截断模板匹配
        t = re.sub(r'-\{([^{}]*)\}-', r'\1', t)
    t = _tmpl(t)
    t = re.sub(r'__\w+__', '', t)                                          # __TOC__
    t = re.sub(r'</?(poem|div|span|center|noinclude|includeonly|onlyinclude|br\s*/?)[^>]*>', '', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r"'''+", '', t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    return t


def norm_lines(t):
    return [s for s in (ln.strip().strip('　').strip() for ln in t.split('\n')) if s]
