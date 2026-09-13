# 内容数据架构设计

> 目标：让收录量无痛扩展，**新增内容只丢文件、跑构建，绝不改应用代码**。这条已验证到 **892 部 / 116,500 篇 / 1.08 亿字**（2026-09-04），期间应用代码未因新增内容改过一行。
>
> 另一条原设想「数据与代码彻底分家、代码仓库永远是小仓库」**未按原样落地**——`base-data` 最终进了 git 并成为唯一源，原因与代价见 §2。

## 0. 一句话总览

**正文用 Markdown（机器与人都可读的内容），结构用 JSON（机器索引）；两者都存 Cloudflare R2，按需 fetch。源 markdown（`base-data`）随仓库长期保留，是改正文与改结构的唯一下手处。**

```
base-data/**.md            build-content              R2 content/                     应用 (React SPA)
（带 frontmatter 的脏 md）  ──解析/拆分/剥字段──▶   JSON 索引 + 纯文本 md      ──按需 fetch──▶  首页/书页/阅读页
（长期源，随仓库提交）        （增量，按门类跑）         （派生产物，应用只读这一片）
```

---

## 1. 拆分原则

> **一篇正文 → 一个纯文本 `.md`（无 frontmatter）；所有结构与元数据 → 3 层 JSON 索引。**

| 数据 | 形态 | 谁产生 | 编辑方式 |
|---|---|---|---|
| 正文 | `.md` 纯文本 | build 从源 md 剥出 | 改 md（覆盖单个文件） |
| 门类 / 书目 / 章节树 | JSON | build 从 frontmatter 汇总 | **改源 md 的 frontmatter**（JSON 每次 build 重生成，手改必被覆盖） |

为什么这样分：正文是连续散文，用 md 才可读、可 diff、可改（避免被压成转义字符串）；目录/树/排序本就是结构化数据，用 JSON 才好被机器索引。各按数据的天然纹理选格式。

---

## 2. 数据生命周期（源在 git，派生在 R2）

```
长期源(git)                 增量构建                 派生产物(R2)
base-data/**.md   ──build──▶  md + JSON  ──upload──▶   R2 content/
（随仓库提交，唯一下手处）                        （应用只读这一片，可随时重建）
```

- **base-data**：带 Hugo frontmatter 的源 md，**长期源**，随代码一起提交（现 120,322 个文件 / 788 MB，`.git` 214 MB）。
- **R2**：派生产物的家，GB 级正是对象存储该干的事。**丢了可以从 base-data 重新 build + upload 重建**。
- **改正文只改 base-data**，然后 `npm run content` + `npm run content:upload`；**不要去改 R2 或 `dist-content` 上的 md/JSON**，下次构建即被覆盖。

> ⚠️ **本节原先写的是反的，2026-09-13 校正**。原设计把 `base-data` 当「整理暂存，上传后从项目删除、不进 git」，把 R2 的 `content/text/**.md` 当长期源。实际演进成了相反，因为**校勘链必须锚在一个带版本历史的源上**：
>
> - `scripts/check-integrity.py`（CI 每次 push 跑）比对断句稿与 `base-data/shushu/mingli/san-ming-tong-hui`，base-data 一删这道闸就失去依据；
> - `data/quotes.json` 的 134 条名句声明「逐字取自站内 base-data 源本」，校验须在 base-data 上原样命中；
> - `docs/collation-log.md` 与 `docs/known-issues.md` 的逐字挂账（讹字、阙文、简体卷）全部按 base-data 路径记录。
>
> 代价是代码仓库不再是「小仓库」。这笔账是认过的：换来的是**每一次改字都留在 git 历史里可查**，与「只删不改不增」那条铁律互为支撑。

### 可编辑的「源」是什么

两类源都在 `base-data`，都在 git 里：

- **正文源** = `base-data/**.md` 的正文部分。
- **结构源** = 同一批 md 的 **frontmatter**（`title` / `weight` / `summary` / `kind`）——门类、书目、章节树由 build 从 frontmatter 汇总。

即「**改正文和改结构都在 base-data 的 md 上**」，build 是唯一的单向通道，没有任何一处需要手抠转义字符串。

---

## 3. R2 对象布局（最终）

```
bucket: chinese-classics
content/
├── manifest.json                                 ← L1 门类总目(极小，启动取)
├── catalog/
│   └── confucius.json                            ← L2 某门类的书目(进门类页取)
├── book/
│   └── confucius/lun-yu.json                     ← L3 某书的章节树(进书取)
└── text/
    └── confucius/lun-yu/xue-er.md                ← 正文(读篇才取，纯文本 md)
```

- R2 key 直接用路径，天然分目录；应用只读 `content/` 这一片。
- **没有第 4 层 chapter JSON**——正文就是 `text/*.md`，其元数据（标题/顺序/上下篇）全在父级 `book.json` 的树里，不重复、不漂移。

---

## 4. ID 规则（地基，路径派生，永不漂移）

规范 ID = 相对 `base-data/` 的路径 slug，去掉数字分批目录、去掉 `.md`。

| 层级 | ID 示例 | 来源 |
|---|---|---|
| 门类 categoryId | `confucius` | 顶层文件夹名 |
| 书 bookId | `confucius/lun-yu` | 门类 + 书目录 |
| 章 chapterId | `confucius/lun-yu/xue-er` | 书 + 篇路径（拍平数字分批目录） |
| 正文 key | `text/confucius/lun-yu/xue-er.md` | `text/` + chapterId + `.md` |

- 数字分批目录（如 `shi-ji/091-120/`）是分页 artifact，**不进 ID**，只用其下文件 `order` 排序。
- ID 全局唯一、稳定。新增任何内容都不改已有 ID（保护链接/书签/R2 对象）。
- 重命名文件夹会改 ID，需要时维护一张 `redirects.json`（旧 ID → 新 ID），属罕见操作。

---

## 5. 目录约定（源 md 怎么放，build 才认）

```
base-data/
  <门类>/                      ← 顶层文件夹 = 一个门类
    _meta.yml                  ← 门类显示信息(name/subtitle/badge/order)
    [ <藏>/<部>/ … ]           ← 「书之上」可有任意层导航(如佛学 经藏→般若部)
      <书>/                    ← 「书」是分片单位(见 §5.1 书边界规则)
        _index.md              ← 书的元信息(title/summary/order)
        <篇>.md                ← 一篇一文件(见 §5.2 拆分粒度)
        [ <卷>/ … ]            ← 书内可再有语义子层(本纪/世家)或数字分批目录
```

层级**不固定**：浅如经部「门类→书→篇」，深如佛学「门类→藏→部→书→卷」。build 不假设固定层数。

### 5.1 书边界规则（深层目录里怎么定位「书」，已实现）

「书」是 catalog 树与 book 树的分界、也是分片单位。一条**递归规则统管深浅所有门类**，自动推导、无需逐门类配置：

1. **折叠数字分批目录** `^\d+-\d+$`（如 `091-120/`、`001-030/`）：分页 artifact，正文子项上提、按 `order` 排。
2. 折叠后，一个目录是**「书」当且仅当它所有子项（子目录 + 文件）的标题都带本目录标题前缀**；否则是**导航层**（门类/藏/部/子类）。
   - 关键信号是**标题前缀**：书的子卷标题带书名前缀（易经→「易经-上经」、史记→「史记 卷119」、四分律→「四分律 卷…」）；导航层的子项是独立书名，不带前缀（阿含部→「长阿含经」、修持→「坐忘论」）。纯结构（含不含子目录）无法区分「书带卷」与「子类带书」——它们同型——所以必须看标题。
   - 目录标题为空时退化为「子项是否有 ≥2 字的共同前缀」（如 `liezi` 无 `_index` 标题，但文件「列子-…」有共同前缀 → 判为书）。
3. 导航层递归处理：子目录继续套用本规则；夹着的单独 `.md` → 各自**自成一本单文件书**（如般若部下的 `jing-gang-jing.md` = 金刚经）。

该规则天然处理变深结构：佛学经藏/论藏有「部」层（藏→部→书），律藏/史传无（藏→书）；同一套规则都对。实测 buddha 178 部 / taoism 39 / mythology 7 全部正确。

> **兜底**：罕见歧义（书的子卷标题未带前缀、或导航层子项恰好共享前缀）由两层保险解决——① build 校验报告标出可疑节点（如目录标题为空）；② 在该节点 `_index.md` 加 `kind: book` / `kind: nav` 显式覆盖，build 优先采用。

### 5.2 拆分粒度（一篇一文件，build 绝不按标题拆）

> **一个源 `.md` = 一个 `text/*.md` = 目录里一个叶子。文件内部的标题（上/下、章）一律保留、内联渲染，不拆成文件。**

为什么不按标题拆：同样是 `###`，在《论语》里是「篇」、在《孟子》里是「篇内上/下」——**标题层级不是可靠信号**。所以拆分粒度由**文件组织**显式决定（整理期一次性定），而非 build 猜测：

- 想要某书篇级可导航 → 存成一篇一文件（孟子已如此：7 篇 7 文件）。
- 短经（大学/中庸/孝经）本就该一整页 → 存成 1 文件 = 1 章。
- 篇内的上/下、章 → 留在该 md 内，前端渲染成页内小标题（可加锚点）。

### 5.3 时间戳来源（`createdAt` / `updatedAt`）

用于「最新收录 / 最近更新 / 按时间排」。**不取 Hugo 的 `date`**——那是录入时间戳、噪声大（史记 130 卷同一天、还有 2021 老日期）。

改由**构建增量状态**维护（与 §11 的 hash 增量是同一份状态，需持久化：体积极小，提交进代码仓库或存 R2）：

```
状态文件 content-state.json：  { id → { hash, createdAt, updatedAt } }
每次 build 对每个 book/chapter：
  · id 首次出现        → createdAt = updatedAt = now
  · 内容 hash 变了     → updatedAt = now（createdAt 不动）
  · 没变              → 两者都不动
```

- 时间格式 ISO8601 UTC（如 `2026-06-28T10:00:00Z`）。
- 书级 `createdAt` = 旗下最早章；`updatedAt` = 最晚章 / 结构变更时间。
- 首次全量迁移时所有条目都记为当次 build 时间；此后新增/改动才产生差异，「最新收录」从那时起有意义。
- 章级时间戳如需（「本篇最近校订」）可给 `TextNode` 加可选 `updatedAt?`，默认先不上。

### 门类 meta（约定驱动，加门类零代码）

每个门类放一个 `_meta.yml`，build 自动扫出来生成 manifest：

```yaml
name: 经部
subtitle: 易 · 诗 · 书 · 礼
badge: 儒家经典
order: 1
```

加新门类 = 新建文件夹 + 一个 `_meta.yml`。**不再有手写的 `categories.ts`。**

### 排序与标题（来自源 md 的 frontmatter，仅 build 时读）

- `order`：取 frontmatter `weight`；缺失则取文件名末尾数字；再缺则按同目录 `date` 排序补 1,2,3…。
- `title`：取 frontmatter `title`，去引号。
- `summary`：取 frontmatter `summary`（非空时）。
- frontmatter 其余字段（`date/tags/draft/showToc/tocOpen/ShowShareButtons/categories`）一律丢弃。
- **输出到 R2 的 `text/*.md` 不带任何 frontmatter**——元数据全归 JSON 索引（单一事实源）。

---

## 6. 三层 JSON 的 Schema

所有对象带 `schemaVersion`，字段尽量可选以便向前扩展。落到 `src/data/types.ts` 前后端共用。

```ts
// ── L1: manifest.json（全站门类总目，极小，启动即取）─────────────
interface Manifest {
  schemaVersion: 1
  generatedAt: string
  categories: CategoryMeta[]
}
interface CategoryMeta {
  id: string          // "confucius"
  name: string        // "经部"
  subtitle?: string
  badge?: string
  order: number
  bookCount: number
}

// ── L2: catalog/<category>.json（门类下导航树，进门类页才取）──────────
// 是「树」而非平铺列表：浅门类(经部)退化成一层 book 节点；
// 深门类(佛学)装下「藏→部→书」多级导航。一套 schema 吃下深浅两种。
interface Catalog {
  schemaVersion: 1
  category: string
  tree: CatalogNode[]
}
type CatalogNode = CatalogCollection | BookRef
interface CatalogCollection {   // 书之上的导航层：藏 / 部
  type: 'collection'
  title: string
  order: number
  children: CatalogNode[]
}
interface BookRef {             // 指向一本书(book/*.json)
  type: 'book'
  id: string          // "confucius/lun-yu"
  title: string
  summary?: string
  author?: string     // 现 _index 多无此字段，预留，后续补
  dynasty?: string    // 成书年代/朝代（≠ 录入时间），预留
  chapterCount: number
  order: number
  variant?: 'trad' | 'simp' | 'mixed'
  createdAt: string   // 首次收录时间，ISO8601 UTC，由构建状态维护(§5.3)
  updatedAt: string   // 最近更新时间，同上
}

// ── L3: book/<category>/<book>.json（一本书的章节树，递归任意深度）──
interface BookDetail {
  schemaVersion: 1
  id: string
  title: string
  summary?: string
  author?: string
  dynasty?: string
  variant?: 'trad' | 'simp' | 'mixed'
  createdAt: string   // 同 BookRef，便于书页直接显示
  updatedAt: string
  nodes: Node[]
}
type Node = CollectionNode | TextNode
interface CollectionNode {     // 目录节点(对应 _index.md)，如「本纪」「卷一」
  type: 'collection'
  title: string
  order: number
  children: Node[]
}
interface TextNode {           // 叶子，指向一篇正文 md
  type: 'text'
  id: string          // chapterId，如 "confucius/lun-yu/xue-er"
  title: string
  order: number
  src: string         // 正文 key，"text/confucius/lun-yu/xue-er.md"
}
```

**没有 L4 chapter JSON。** 正文是 `text/*.md`，渲染一篇 = 父级 `book.json`（拿标题/树/上下篇）+ 该篇 `.md`（纯正文）。

---

## 7. 分片策略（抗规模关键）

| 请求时机 | 取的对象 | 体积特性 |
|---|---|---|
| 打开首页 | `manifest.json` | 永远小（仅门类数十条） |
| 进门类页 | `catalog/<门类>.json` | 单门类书目，受控 |
| 进书 | `book/<id>.json` | 单书目录树（仅元数据，几十 KB 级） |
| 读篇 | `text/<id>.md` | 单篇正文，几 KB |

**无论收录涨到多大，单次请求体积都恒定。** 绝不做「一个 manifest 装下所有书」。
（边界：单本书叶子达数万时 `book.json` 才需分片——本项目语料到不了，暂不处理。）

---

## 8. 各种源结构 → 同一布局

**一篇一文件、build 不按标题拆**（§5.2），所以每个源 `.md` 直接对应一个 `text/*.md`：

| 书 | 源 md 现状 | build 动作 | 产出 |
|---|---|---|---|
| 孟子 | 7 个文件(一篇一个) | 一文件=一章，篇内 `### 上/下` 内联保留 | 7 个 `text/*.md` + 树 |
| 诗经 | 306 个 `shi-jing-NNN.md` | 一文件=一篇，剥 frontmatter | 305 个 `text/*.md` + 树 |
| 左传 | 12 个 `...-gong.md` + 子目录 | 目录→collection，文件→text | `text/*.md` + 嵌套树 |
| 论语 | 1 个 `lun-yu.md`（20 篇塞一起） | **整理期先拆成 20 篇文件**（§13），之后一文件=一章 | 20 个 `text/*.md` + 树 |

不管源是 1 个还是 300 个、平铺还是嵌套，产物统一是 `book.json`(树) + `text/*.md`(正文)。

### 深层门类示例：佛学（门类→藏→部→书→卷）

```
catalog/buddha.json            tree: 经藏→般若部→{大般若经, 金刚经, 心经} … 律藏 …（导航树，只到书）
book/buddha/jingzang/bore/da-bore.json          大般若经：600 个 text 节点(数字批次已折叠)
book/buddha/jingzang/bore/jing-gang-jing.json   金刚经：单文件书
text/buddha/jingzang/bore/da-bore/bore-001.md   卷001 正文
```

- 书之上的「藏/部」落进 **catalog 树**；书之下的「卷」落进 **book.json 树**；分界由 §5.1 书边界规则自动判定。
- bookId 用全路径 slug（`buddha/jingzang/bore/da-bore`），深但唯一稳定。
- `catalog/buddha.json` 只到**书**这层（几百个 book 引用 + 藏/部节点），不含卷正文，几十～一两百 KB，仅进「佛学」时取。

---

## 9. 上一篇 / 下一篇

**书内导航，不跨书。** 实现 = 把 `book.json` 的 `nodes` 树**深度优先、每层按 `order` 排**拍平成线性序列，取当前位置 ±1。

```js
const flat = flatten(book.nodes)               // 进书拿到 book.json 后拍平一次
const i = flat.findIndex(n => n.id === current)
prev = flat[i - 1]                             // {id, title, src}，到首篇为 undefined
next = flat[i + 1]                             // 到末篇为 undefined → 显示「已是最后一篇·返回目录」
```

- **零额外请求、零额外存储**：进书时已加载 `book.json`，上下篇的标题与链接都在其中。
- 嵌套书自动跨 collection 边界 → 「连续往下读」。
- 不在 build 时预埋 `prevId/nextId`，避免冗余与重排维护成本。

---

## 10. 内容更新与缓存

- **改正文** = 改 `base-data/**.md` 的正文，再 `npm run content` + `npm run content:upload`。
  - ⚠️ **不要直接改 R2 上的 `content/text/*.md`**（`wrangler r2 object put`、`rclone sync` 都算）。
    那样改出来的字**不留 git 历史、不过 `check-integrity.py`、与 collation-log 的逐字挂账脱节**，
    且下一次 build+upload 会把它默默覆盖回去。本节原先教的正是这个做法，2026-09-13 已改正。
- **改结构**（书名/排序/分类）= 改源 md 的 frontmatter（`title`/`weight`/`summary`/`kind`），
  **不改 JSON**——`dist-content` 与 R2 上的 JSON 每次 build 都重生成。
- **缓存**：`text/*.md` 设较短 `Cache-Control` TTL；需立即生效时覆盖后 purge。
  （强一致可选：在 `book.json` 的 text 节点加 `rev` 短 hash，正文按 `?v=<rev>` 取；默认先不上这层。）

---

## 11. 构建流程（`scripts/build-content.mjs`）

```
base-data/**.md (长期源)
   │ 1. 递归扫描，跳过 .DS_Store；折叠数字分批目录(§5.1)
   │ 2. 顶层→门类(_meta.yml)；按书边界规则(§5.1)定位「书」，书之上入 catalog 树、书之下入 book 树
   │ 3. 解析 frontmatter：title/order/summary 进 JSON；探测繁简写 variant；其余丢弃
   │ 4. 正文：一源文件=一 text md(不按标题拆，§5.2)；剥掉 frontmatter，输出纯文本 md
   ▼
dist-content/  (镜像 R2 的 content/ 布局，gitignore)
   │ 5. 校验报告：缺 _index、排序冲突、空正文、ID 碰撞、孤儿文件、书边界可疑节点(§5.1)
   │ 6. 增量上传变化对象到 R2(wrangler r2 / SDK)
   ▼
R2 content/
```

- 产物可随时从源重建；增量按文件 hash，只重出+只上传**变化**的对象。
- 同一份 hash 状态(`content-state.json`)顺带维护 `createdAt/updatedAt`(§5.3)，须持久化(提交进仓库或存 R2)。
- 可挂 CI：push 触发构建 + 上传。

---

## 12. 向前兼容约定

- 每个对象带 `schemaVersion`。
- **只增不改**：新增字段一律可选；不改已有字段含义；不删字段（弃用就停止写入）。
- 前端对未知字段宽容忽略；对缺失字段给默认值。
- 老 JSON 与新前端、新 JSON 与老前端均可共存，分批迁移无忧。

---

## 13. 数据清洗待办（扫描发现的不规整）

| 问题 | 现状 | 处理 |
|---|---|---|
| `lun-yu.md` 整本一文件 | 20 篇塞进 1 个文件(20 个 `###`) | 整理期拆成 20 个篇文件，对齐「一篇一文件」约定(§5.2) |
| `butterfly/` 缺「书」层 | 33 篇庄子直接平铺在门类下 | 规整为 `<门类>/zhuangzi/*.md` |
| 门类 ID 不对齐 | base-data 12 门类 vs 旧 `categories.ts` 6 个 | 以 base-data 目录为准，建 `_meta.yml` |
| `draft: true` 占 95% | Hugo 草稿标记 | build 一律忽略（不进产物） |
| `date` 是录入时间戳 | 噪声大（整批同一天/2021 老日期） | 不进产物；「最新收录/更新」改由构建状态维护 `createdAt/updatedAt`(§5.3) |
| 繁简混用 | 繁 6823 / 简 2201 文件 | 源不动，build 探测写 `variant`；前端做可选繁简切换(OpenCC) |
| 散落 `.DS_Store` | 已 gitignore 但树里存在 | build 跳过 |
| 平铺书缺 `weight` | 如 butterfly | 按同目录 `date` 排序补 `order` |

---

## 14. 应用改造点

| 现状 | 改为 |
|---|---|
| `src/data/categories.ts` 手写门类 | 从 `manifest.json` 读 |
| `src/data/books.ts` 3 本占位硬编码 | 改为按需 fetch + 内存缓存的 loader |
| `Reader.tsx` 从 `getBook()` 取 | 取 `book.json` + `text/*.md`；上下篇由 book 树拍平推导 |
| `wrangler.toml` | 启用预留的 R2 binding（`BOOKS` / `chinese-classics-content`）与 Worker `/api/*` 代理 |

组件接口基本不变，主要换数据来源。前端需一个轻量 md 渲染（先「按空行分段」，将来要富格式再换解析器）。

---

## 15. 补录工作流（增量 + 已收录/新收录识别）

```
1. 往 base-data/<门类>/<新书>/ 丢符合约定的 md（新书 = git 里显示为未跟踪 ??）
2. npm run content      # = build-content --all（打印「本次变更」）+ gen-readme（刷新 README）
3. npm run content:upload   # 只传新增/改动的文件，跳过未变（按内容哈希）
4. git add -A && commit && push → 自动部署
—— 全程不碰一行应用代码 ——
```

npm 脚本：`content:build`(构建全部门类) · `readme`(刷新 README) · `content`(两者) · `content:upload`(增量上传)。

**底本选择原则**：新增或重收录典籍时，先确认底本来源与版本性质。优先采用可追溯的专书版本、早期刻本影印、权威点校/校注本，或有清晰来源说明的数字化项目；尽量不以清代官修、总集式、丛书式汇总文库作正文主底本，尤其是《四库全书》系统以及清代编纂的总集/全集/类书。此类来源常见避讳改字、抽换、删削、重编、误收与无句读问题，可作补缺或对校材料，不宜作为默认主源。

若某书暂时只能取得清代汇总本，应在收录说明或跟踪 issue 中明示：主底本名称、采用原因、可能的避讳/删削风险、已对校来源；并把该书列为后续换源或校勘候选。不要为了统一字形、补标点或补缺而静默改写正文，涉及异文取舍时保留记录。

**README 自动生成**：`scripts/gen-readme.mjs` 从 `dist-content` 读 manifest+catalog，生成 `README.md` 的收录概况(门类/部数/篇数)与全量目录。**勿手改 README**，内容变动跑 `npm run readme` 即刷新——这样"随时更新、保持最新"。

**怎么区分「已收录」与「新收录」**，三重信号：

- **构建变更报告**：每次 `build-content` 打印本轮「新收录 / 有改动 / 未变」的书 id（最直观）。
- **`content-state.json`**（随仓库提交）：每本书一条 `{hash, createdAt, updatedAt}`。在册=已收录；不在=全新；`createdAt` 即首次收录时间，`updatedAt>createdAt` 即被补录改过。
- **git 状态**：base-data 里新丢的文件显示为未跟踪 `??`，一眼看出哪些还没纳入。

**增量上传**：`build` 产出 `dist-content/.files.json`（每个产物文件的内容哈希）；`upload-r2-s3.mjs` 拿它与本地 `.r2-uploaded.json`（已传哈希）对比，**只上传哈希变了的文件**。实测改一篇正文 → 仅 4 个文件上传（该篇 + 其 book.json + catalog + manifest），而非全量 117,430。

> `.r2-uploaded.json` 是本地缓存（gitignore，丢了重传即可）；`content-state.json` 才是随仓库走的「收录台账」。
> 上传走 R2 的 S3 接口（SigV4），凭据取 `.env.local` 的 `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`，无 Cloudflare API 的 ~4/s 限流，默认并发 24。
> 旧的 `upload-r2.mjs`（走 Cloudflare API、并发 3）已于 2026-09-13 删除。

---

## 16. 未来口子（暂不实现，结构上先不堵死）

- **搜索**：上万章后客户端搜不动 → 预生成倒排索引分片，或 Worker 服务端搜。正文已是干净 md，建索引不返工。
- **跨书续读**：书末跳下一本，需读 `catalog.json` + 下一本 `book.json`。当前只做书内。
- **多版本/校勘**：白文/注疏/译文 → 加 `edition` 维度，同 `variant` 思路。
- **注释 / 拼音 / 异体字**：作为渲染层叠加或 sidecar 文件，正文 md 保持干净。
- **编辑后台**：网页可视化改 md → Worker 写回 R2。

---

## 落地阶段

1. ✅ 本文档定稿（md 正文 + JSON 索引版）。
2. ✅ 定三层 schema 的 TS 类型 → `src/data/types.ts`（前后端共用）。
3. ✅ 写 `scripts/build-content.mjs`，先拿 `confucius` 跑通三种结构 + 校验报告。
4. ✅ 全量构建，修 §13 清洗项。
5. ✅ 前端 loader 改造，先用本地 `dist-content/` 联调。
6. ✅ 接 R2 + Worker `/api/*`，上线（https://chinese-classics.org）。

> 本阶段表已全部完成；此后的演进（按门类增量构建、S3 接口上传、边缘渲染 SEO、名句库 D1）
> 见 `docs/seo.md` 与 `docs/collation-log.md`。
