// 内容数据的「形状合约」：build 脚本(生产方)与前端(消费方)共用，
// 保证两端对同一套 JSON 结构强一致。权威设计见 docs/data-architecture.md §6。
// 这里只定义类型，不含任何逻辑。

/** 当前 schema 版本，向前兼容用：只增字段、不改含义。 */
export type SchemaVersion = 1

/** 繁简变体标记，由 build 探测正文写入。 */
export type Variant = 'trad' | 'simp' | 'mixed'

// ─────────────────────────────────────────────────────────────
// L1: manifest.json —— 全站门类总目（极小，启动即取）
// ─────────────────────────────────────────────────────────────
export interface Manifest {
  schemaVersion: SchemaVersion
  /** 本次构建时间(ISO8601 UTC)，非内容时间 */
  generatedAt: string
  categories: CategoryMeta[]
}

export interface CategoryMeta {
  /** 门类 ID = 顶层文件夹名，如 "confucius" */
  id: string
  /** 显示名「经部」，来自 _meta.yml */
  name: string
  subtitle?: string
  badge?: string
  order: number
  /** 该门类书数量(build 算) */
  bookCount: number
}

// ─────────────────────────────────────────────────────────────
// L2: catalog/<category>.json —— 门类导航树（进门类页才取）
// 是「树」而非平铺列表：浅门类(经部)退化成一层 book 节点；
// 深门类(佛学)装下「藏→部→书」多级导航。
// ─────────────────────────────────────────────────────────────
export interface Catalog {
  schemaVersion: SchemaVersion
  /** 门类 ID */
  category: string
  tree: CatalogNode[]
}

export type CatalogNode = CatalogCollection | BookRef

/** 书之上的导航层：藏 / 部 */
export interface CatalogCollection {
  type: 'collection'
  title: string
  order: number
  children: CatalogNode[]
}

/** 指向一本书(book/*.json) */
export interface BookRef {
  type: 'book'
  /** bookId，路径 slug，如 "confucius/lun-yu" */
  id: string
  title: string
  summary?: string
  /** 作者，源数据暂无，预留 */
  author?: string
  /** 成书年代/朝代(≠ 录入时间)，预留 */
  dynasty?: string
  /** 篇/卷数 = text 叶子总数 */
  chapterCount: number
  order: number
  variant?: Variant
  /** 首次收录时间(ISO8601 UTC)，由构建状态维护，见 §5.3 */
  createdAt: string
  /** 最近更新时间(ISO8601 UTC) */
  updatedAt: string
}

// ─────────────────────────────────────────────────────────────
// L3: book/<category>/<book>.json —— 一本书的章节树（进书才取）
// ─────────────────────────────────────────────────────────────
export interface BookDetail {
  schemaVersion: SchemaVersion
  /** bookId */
  id: string
  title: string
  summary?: string
  author?: string
  dynasty?: string
  variant?: Variant
  createdAt: string
  updatedAt: string
  nodes: BookNode[]
}

export type BookNode = BookCollection | BookText

/** 书内分卷节点(对应 _index.md)，如「本纪」「萬章上」 */
export interface BookCollection {
  type: 'collection'
  title: string
  order: number
  children: BookNode[]
}

/** 叶子：指向一篇正文 md */
export interface BookText {
  type: 'text'
  /** chapterId，如 "confucius/lun-yu/xue-er" */
  id: string
  title: string
  order: number
  /** 正文 md 的 R2 key，如 "text/confucius/lun-yu/xue-er.md" */
  src: string
}

// ─────────────────────────────────────────────────────────────
// L4: text/<category>/<book>/<chapter>.md —— 纯正文，无字段、无 frontmatter。
// 元数据全在上面的 book.json 里，故此处无对应类型。
// ─────────────────────────────────────────────────────────────
