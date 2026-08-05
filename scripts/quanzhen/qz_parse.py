# -*- coding: utf-8 -*-
"""全真批·共用原语：底本读取、节切分、体裁组白名单、裸行式篇题判据。

装配逻辑在 qz_books.py。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CACHE = os.environ.get('QZ_CACHE', 'dzcache')

# ── 体裁组白名单：命中者剥去不入篇名；其余空节一律视为词牌，以「词牌·篇题」并入 ──
GENRE = set('''七言律詩 七言長篇 五言律詩 五言長篇 藏頭七言長篇 七言絕句 五言絕句
詞 詞（藏頭） 歌詞詩 詩 碑文 頌（三首） 古調（十五首） 五言短句（三首）
七言詩（藏頭） 五言詩（藏頭） 七言古詩 五言古詩 六言詩 四言詩 三言詩'''.split())

# ── 洞玄金玉集/雲光集 裸行式篇题：含逗顿者默认判正文；下列两条经逐条回查确为长篇题 ──
BARE_TITLE_WHITELIST = {
    '因覽鄠縣件壽之與眾道友，唱和楊清叟束軒籜龍過毋自適詩卷。借韻各賦一篇',
    '醵博州荏平丁家塊務酒官，轉與老姚仙飲',
}
TERM, CONT = '。！？」』', '，、；：'



def load(book):
    return json.load(open(os.path.join(CACHE, book + '.json')))


def sections(text):
    """切成 [(级, 标题, 原始正文)]；首段无标题者以 (0, None, …) 返回。"""
    parts = re.split(r'^(={2,6})\s*(.+?)\s*=*\s*$', text, flags=re.M)
    out = [(0, None, parts[0])]
    for i in range(1, len(parts), 3):
        out.append((len(parts[i]), parts[i + 1].strip(), parts[i + 2]))
    return out
