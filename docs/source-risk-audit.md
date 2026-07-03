# 底本来源风险清单

> 2026-07-03 扫描 `base-data/`、`dist-content/catalog/` 与 `docs/known-issues.md` 后整理。本文只记录与“四库、清代总集/选本、整体数字文库”有关的存量风险；普通正文中偶然提到“四库”“文渊阁”等不计入底本风险。

## 1. 优先复核或换源

| 书 | 位置 | 规模 | 证据 | 风险判断 | 建议 |
|---|---|---:|---|---|---|
| 临川文集 | `base-data/literature/lin-chuan-wen-ji/` | 101 篇 / 412,268 字 | 99 个正文文件残留“钦定四库全书”；`玄=0`、`弘=0`，且有“元孙”等疑似避讳改字 | 高。可读性影响有限，但原文字面、检索、人名/专名与校勘引用均受影响 | 优先更换为可追溯专书本，如四部丛刊、宋元明刻影印或现代点校本；换源前引用需注明四库系底本 |
| 宋书 | `base-data/history/song-shu/001-030/song-shu-019.md` 至 `song-shu-022.md` | 整书 100 篇；明确残留在卷 19-22 | 卷 19-22 混入卷末“考證/注釋”块；卷 21 另混入“欽定四庫全書薈要訂正” | 局部污染。暂不能证明整书取自四库荟要，但这些卷含非正文校订块 | 已从正文移除卷末校语和网页脚注，处理依据见 `docs/collation-log.md`；后续可与点校本/百衲本抽校 |
| 元史 | `base-data/history/yuan-shi/031-060/yuan-shi-031.md` | 整书 210 篇；明确残留在卷 31 | 正文中混入“摛澡堂四庫全書薈要 （明）宋濂 元史·卷三十一.p151[1]” | 局部污染。像来源页脚/脚注，不是原文 | 已删除来源题注行，处理依据见 `docs/collation-log.md`；后续可抽校专名异文 |
| 神异经 | `base-data/mythology/zhiguai/shen-yi-jing/` | 1 篇 / 3,592 字 | `_index.md` 明示“按四库本篇目边界”，并参考《汉魏丛书》断句 | 中低。主要影响篇目边界与取舍，不像整部正文直接四库化 | 保留现状可读；若追求文本完整，应另列《汉魏丛书》/《广汉魏丛书》本对校 |
| 近思录 | `base-data/masters/jin-si-lu/` | 15 篇 / 52,732 字 | 当前说明为维基文库句读白文本；已知问题记录曾以四库本补缺 | 低。主底本已换出四库，风险集中在补缺条目 | 标记补缺处，后续用朱子语类/通行点校本抽校 |

## 2. 清代总集来源

这些书的 `_index.md` 明示“据《全唐诗》辑录”。《全唐诗》为清康熙朝官修总集，当前扫描未见系统性避讳替换迹象（仍保留大量“玄”“弘”），但归属、重出、漏收、误收与异文风险中等。

| 书 | 位置 | 规模 | 风险判断 | 建议 |
|---|---|---:|---|---|
| 王右丞集 | `base-data/literature/wang-you-cheng-ji/` | 403 篇 / 25,057 字 | 清代总集辑录，单篇字面风险低，归属/异文风险中 | 后续换王维专集或点校本 |
| 李太白集 | `base-data/literature/li-tai-bai-ji/` | 1,206 篇 / 105,495 字 | 同上 | 后续换李白专集或点校本 |
| 杜工部集 | `base-data/literature/du-gong-bu-ji/` | 1,489 篇 / 126,281 字 | 同上；另有个别《四库提要》评价作为正文校语 | 后续换杜诗专集或点校本 |
| 白氏长庆集 | `base-data/literature/bai-shi-chang-qing-ji/` | 3,008 篇 / 227,450 字 | 同上，且部分篇题/校语已体现《全唐诗》归属争议 | 后续换白居易专集或点校本 |

## 3. 清代选本，本身是收录对象

这些不是“拿清代汇总库当古书底本”的污染，而是作品本身就是清人编选或清代通行选本。若目标是读该选本，应保留；若目标是还原作者全集或原文定本，不应以它们替代专书底本。

- 唐诗三百首：`base-data/literature/tang-shi-san-bai-shou/`
- 宋词三百首：`base-data/literature/song-ci-san-bai-shou/`
- 古文观止：`base-data/literature/gu-wen-guan-zhi/`
- 千家诗：`base-data/literature/qian-jia-shi/`，传统童蒙选本，含王相选注系统，按选本保留即可。

## 4. 非清代，但属于整体数字库质量风险

这组不属于清代避讳/四库删改，但已经确认存在整体数字文库的占位、缺字或无句读问题，后续也应优先换更可追溯底本。

### 殆知阁医藏来源

`docs/known-issues.md` 记录医家门类取自殆知阁医藏，存在 `KT`、空格吞字、低标点长段等问题。

- 黄帝内经：`base-data/medicine/huangdi-neijing/`
- 伤寒论：`base-data/medicine/shang-han-lun/`
- 金匮要略：`base-data/medicine/jin-kui-yao-lue/`
- 难经：`base-data/medicine/nan-jing/`
- 神农本草经：`base-data/medicine/shen-nong-ben-cao-jing/`
- 本草纲目：`base-data/medicine/ben-cao-gang-mu/`
- 诸病源候论：`base-data/medicine/zhu-bing-yuan-hou-lun/`
- 备急千金要方：`base-data/medicine/bei-ji-qian-jin-yao-fang/`
- 肘后备急方：`base-data/medicine/zhou-hou-bei-ji-fang/`
- 脾胃论：`base-data/medicine/pi-wei-lun/`
- 格致余论：`base-data/medicine/ge-zhi-yu-lun/`
- 温病条辨：`base-data/medicine/wen-bing-tiao-bian/`
- 四圣心源：`base-data/medicine/si-sheng-xin-yuan/`
- 濒湖脉学：`base-data/medicine/bin-hu-mai-xue/`
- 针灸甲乙经：`base-data/medicine/zhen-jiu-jia-yi-jing/`
- 汤头歌诀：`base-data/medicine/tang-tou-ge-jue/`
- 医学三字经：`base-data/medicine/yi-xue-san-zi-jing/`
- 洗冤集录：`base-data/medicine/xi-yuan-ji-lu/`

### 现代汇编来源

以下 22 部词集据《全宋词》辑录。《全宋词》为现代唐圭璋编纂，不属清代避讳风险；但如果项目目标转为“专书定本”，仍应与各家别集或权威点校本复校。

- 乐章集、张子野词、珠玉词、六一词、东坡词、小山词、山谷词、淮海词、东山词、清真集、樵歌、漱玉词、放翁词、稼轩词、白石道人歌曲、梅溪词、后村长短句、梦窗词、草窗词、碧山词、竹山词、山中白云词。
