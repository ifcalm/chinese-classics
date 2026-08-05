# -*- coding: utf-8 -*-
"""欧阳修集·落盘 base-data/literature/ouyang-xiu-ji/。

体例同王临川集/东坡全集：一卷一子目录、一篇一文件。诗词集若按卷并成单文件，
Reader 的 isVerse() 遇标题即不居中，且 .reader__text 无 pre-wrap 会把单换行塌缩。
标题一律简体（站点铁律），正文保持底本繁体。
weight 取生年 1006，置《六一词》(1007) 前一位，诗文在前词在后，同东坡全集/东坡词例。
"""
import os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oy_parse import parse

ROOT = os.environ.get('OY_ROOT', 'base-data/literature/ouyang-xiu-ji')
SIMP_CACHE = os.environ.get('OY_SIMP', 'oy-simp.json')

# 齐言联句拆行：底本常把两联挤在一行，站内体例(王临川集/唐诗三百首)是一联一段。
# 只改换行不动字，汉字流不变。
#
# ⚠ 判据必须是**真·齐言**：全行各联的上下句字数全部相等。
# 只看「有逗有句」会误伤四六骈文——卷083 内制集口宣「卿等並持使節，協講鄰歡。
# 飭車馭以載勞，及疆亭而茲喜。」是 6+4、6+6、4+4，一度被当成诗拆开。
# 等长这一条即可把骈文排除干净：全书扫过，放宽到任意等长后新增的只有
# 神道碑墓志的四言铭辞、墓志的三言铭辞、内制集的春帖子词，皆韵文，拆之为是。
RE_PAIR = re.compile(r'([^，。！？；：、（）「」]+)，([^，。！？；：、（）「」]+)[。！？]')
RE_NOTE = re.compile(r'（[^（）]*）')


def _couplets(seg):
    """整段恰好由等长齐言联组成则返回诸联，否则返回 None。"""
    pos, out, lens = 0, [], set()
    for m in RE_PAIR.finditer(seg):
        if m.start() != pos:
            return None
        out.append(m.group(0))
        lens.add(len(m.group(1)))
        lens.add(len(m.group(2)))
        pos = m.end()
    if pos != len(seg) or len(out) < 2 or len(lens) != 1:
        return None
    return out if 3 <= lens.pop() <= 8 else None


def split_couplets(lines):
    """拆齐言联；夹注（…）不参与判定，切分时归其所在／紧随之联。"""
    out = []
    for ln in lines:
        flat = RE_NOTE.sub('', ln)
        cps = _couplets(flat) if len(flat) > 18 else None
        if not cps:
            out.append(ln)
            continue
        # flat 第 k 字在原行中的位置；夹注可插在联中(凋零鶯穀友，（…）憔悴雁池邊。)，
        # 故不能用字符串查找，须逐字走位。
        pmap, k = [], 0
        while k < len(ln):
            m = RE_NOTE.match(ln, k)
            if m:
                k = m.end()
                continue
            pmap.append(k)
            k += 1
        buf, at, prev = [], 0, 0
        for c in cps:
            at += len(c)
            end = pmap[at - 1] + 1
            while True:                                # 紧随其后的夹注归前一联
                m = RE_NOTE.match(ln, end)
                if not m:
                    break
                end = m.end()
            buf.append(ln[prev:end])
            prev = end
        if prev < len(ln):
            buf[-1] += ln[prev:]
        out += [x.strip() for x in buf if x.strip()]
    return out


def fm(**kw):
    body = ['---']
    for k, v in kw.items():
        if v is not None:
            body.append('%s: %s' % (k, '"%s"' % v if isinstance(v, str) else v))
    return '\n'.join(body + ['---']) + '\n'


def main():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'quanzhen'))
    os.environ.setdefault('QZ_SIMP_CACHE', SIMP_CACHE)
    from qz_simp import to_simp            # 复用全真批的繁→简批量转换（variant=zh-hans）
    vols, _ = parse()
    titles = [v['title'] for v in vols]
    titles += [p['title'] for v in vols for p in v['pieces']]
    simp = to_simp(titles)

    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    open(os.path.join(ROOT, '_index.md'), 'w').write(fm(
        title='欧阳修集', kind='book', weight=1006, date='2026-08-01',
        tags='["集部", "宋"]', draft='true',
        summary='北宋·欧阳修诗文全集，一百五十三卷附补遗与附录五种。'
                '居士集、居士外集、易童子问、外制内制集、奏议、河东河北奉使奏草、'
                '濮议、崇文总目叙释、于役志、归田录、诗话、笔说、试笔、近体乐府、'
                '集古录跋尾、书简，宋人所编十种俱全。'
                '据维基文库《欧阳修集》收录（繁体，有新式标点）；'
                '底本玄弘匡胤皆不避讳、无馆臣痕迹，非四库系。'
                '底本有 GB/Big5 转换损坏，已以四库本《文忠集》为证人回改 117 处，'
                '另 23 处证人亦缺字者存照挂账，详 docs/collation-log.md。',
        showToc='false', tocOpen='false', ShowShareButtons='false'))

    for vi, v in enumerate(vols, 1):
        vdir = os.path.join(ROOT, '%03d' % vi)
        os.makedirs(vdir)
        open(os.path.join(vdir, '_index.md'), 'w').write(
            fm(title=simp.get(v['title'], v['title']), weight=vi))
        w = max(2, len(str(len(v['pieces']))))
        for pi, p in enumerate(v['pieces'], 1):
            t = simp.get(p['title'], p['title']).replace('"', '”')
            open(os.path.join(vdir, '%0*d.md' % (w, pi)), 'w').write(
                fm(title=t, weight=pi) + '\n' + '\n\n'.join(split_couplets(p['lines'])) + '\n')
    print('落盘：%d 卷 · %d 篇' % (len(vols), sum(len(v['pieces']) for v in vols)))


if __name__ == '__main__':
    main()
