// SEO 元数据派生规则 —— 全站唯一事实源。
// Worker 边缘渲染(worker.ts)与前端 document.title 同步共用此模块，
// 保证爬虫看到的与用户看到的标题永远一致。规则本身即「SEO 数据模型」：
// 新增任何书/门类走正常 content:build 即自动适配，无需逐篇配置。

export const SITE_NAME = '古典文库'
export const SITE_TITLE = '古典文库 · Chinese Classics'
export const SITE_URL = 'https://www.chinese-classics.org'
export const SITE_DESC = '经 · 佛 · 道 · 史 · 医 · 集 · 神话，一处可读可搜的中国古典文库。'

/** 章节展示名：build 产物的章节 title 多带「书名-」前缀(如「庄子-逍遥游」)，
    页面标题里书名单列，须剥前缀避免「庄子-逍遥游 · 庄子」的赘余。 */
export function chapterDisplayTitle(bookTitle: string, chapterTitle: string): string {
  return chapterTitle.startsWith(bookTitle + '-')
    ? chapterTitle.slice(bookTitle.length + 1)
    : chapterTitle
}

export const chapterPageTitle = (bookTitle: string, chapterTitle: string) =>
  `${chapterDisplayTitle(bookTitle, chapterTitle)} · ${bookTitle} | ${SITE_NAME}`

export const bookPageTitle = (bookTitle: string) => `${bookTitle}目录 | ${SITE_NAME}`

export const categoryPageTitle = (name: string) => `${name} | ${SITE_NAME}`

/** 章节 description = 正文剥标记后前 110 字。派生自内容本身，无需人工维护。 */
export function descriptionFromText(md: string, max = 110): string {
  const plain = md
    .replace(/```[a-z]*\n?[\s\S]*?```/g, ' ') // 卦象等代码块
    .replace(/^#{1,6}\s.*$/gm, ' ') // 小节标题
    .replace(/^>\s?/gm, '') // 引用标记
    .replace(/\s+/g, ' ')
    .trim()
  return plain.length > max ? plain.slice(0, max) + '…' : plain
}

export function bookDescription(title: string, summary: string | undefined, chapterCount: number): string {
  const tail = `《${title}》全文在线阅读，共 ${chapterCount} 篇，支持竖排与夜读。`
  return summary ? `${summary} ${tail}` : tail
}

export const categoryDescription = (name: string, bookCount: number) =>
  `${name}典籍 ${bookCount} 部，全文在线阅读。${SITE_DESC}`
