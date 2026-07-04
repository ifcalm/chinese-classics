# 幽冥问答录(民国特例收录,用户拍板) ← 善书网原文(简体新式标点),灵栖/奥秘世界两源逐条交叉验证(81问一一对应)。
# 结构:序(1944 云照坤序)+问答八十一则+读书后(杜之英六则见闻及跋,1944,与原书同刊,保留)。
# python3 parse-ymwdl.py [--write]
import re, sys, json, os

S = os.path.join(os.path.dirname(__file__), 'ymwdl')
DEST = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/mythology/zhiguai/you-ming-wen-da-lu'
WRITE = '--write' in sys.argv
han = lambda s: len(re.findall(r'[㐀-鿿]', s))

t = open(os.path.join(S, 'shanshu.txt'), encoding='utf-8').read()
paras = [l.strip() for l in t.split('\n') if l.strip()]

i_q1 = next(i for i, l in enumerate(paras) if l.startswith('一问：'))
i_sh = next(i for i, l in enumerate(paras) if l.startswith('读《幽冥问答录》书后'))

xu = paras[1:i_q1]            # 掐掉行0「序」标题
wenda = paras[i_q1:i_sh]
shuhou = paras[i_sh + 1:]     # 掐掉标题行

# 校验:81问、问答成对、跋署收尾
qs = [l for l in wenda if re.match(r'^[一二三四五六七八九十〇○]+问：', l)]
assert len(qs) == 81, f'问答条数 {len(qs)} != 81'
assert qs[-1].startswith('八一问'), qs[-1]
assert '杜之英敬识' in shuhou[-1], shuhou[-1]
print(f'序:{len(xu)}段 {han("".join(xu))}字 | 问答:{len(wenda)}段 81问 {han("".join(wenda))}字 | 书后:{len(shuhou)}段 {han("".join(shuhou))}字')
print('残留:', len(re.findall(r'\{\{|\}\}|\[\[|<[a-z]', ''.join(paras))))

def fm(d):
    out = '---\n'
    for k, v in d.items():
        out += f'{k}: {v}\n' if isinstance(v, int) else f'{k}: {json.dumps(v, ensure_ascii=False)}\n'
    return out + '---\n'

if WRITE:
    import shutil
    shutil.rmtree(DEST, ignore_errors=True)
    os.makedirs(DEST)
    open(f'{DEST}/_index.md', 'w').write(fm({
        'title': '幽冥问答录', 'weight': 70, 'kind': 'book',
        'summary': '民国·黎澍（1883—1954）口述，林黝襄问录，1944 年刊行。黎氏自述清末尝任冥判，以八十一则问答记幽冥见闻，附杜之英书后六则。志怪问答体之近世遗响，特例收录（本站以清亡为收录下限，此书与《人间词话》同为特例）。'
    }))
    open(f'{DEST}/00-xu.md', 'w').write(fm({'title': '序', 'weight': 0}) + '\n' + '\n\n'.join(xu) + '\n')
    open(f'{DEST}/01-wenda.md', 'w').write(fm({'title': '问答八十一则', 'weight': 1}) + '\n' + '\n\n'.join(wenda) + '\n')
    open(f'{DEST}/02-shuhou.md', 'w').write(fm({'title': '读《幽冥问答录》书后', 'weight': 2}) + '\n' + '\n\n'.join(shuhou) + '\n')
    print('已写入', DEST)
