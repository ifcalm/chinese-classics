// 内容 loader：按需 fetch dist-content 的 JSON/md，带内存缓存。
// 本地 dev 从 /content（软链到 dist-content）取；将来换 R2 只需改 BASE。
import type { Manifest, Catalog, BookDetail, BookNode, BookText, CatalogNode, BookRef } from './types'

// dev 走本地软链 /content；部署时用 VITE_CONTENT_BASE 指向 R2 公共域或 Worker /api
const BASE = import.meta.env.VITE_CONTENT_BASE ?? '/content'

const jsonCache = new Map<string, Promise<unknown>>()
function getJson<T>(key: string): Promise<T> {
  let p = jsonCache.get(key)
  if (!p) {
    p = fetch(`${BASE}/${key}`).then((r) => {
      if (!r.ok) throw new Error(`加载失败 ${key}: ${r.status}`)
      return r.json()
    })
    jsonCache.set(key, p)
  }
  return p as Promise<T>
}

export const getManifest = () => getJson<Manifest>('manifest.json')
export const getCatalog = (category: string) => getJson<Catalog>(`catalog/${category}.json`)
export const getBook = (bookId: string) => getJson<BookDetail>(`book/${bookId}.json`)

const textCache = new Map<string, Promise<string>>()
export function getChapterText(src: string): Promise<string> {
  let p = textCache.get(src)
  if (!p) {
    p = fetch(`${BASE}/${src}`).then((r) => {
      if (!r.ok) throw new Error(`加载正文失败 ${src}: ${r.status}`)
      return r.text()
    })
    textCache.set(src, p)
  }
  return p
}

/**
 * chapterId → 所属 bookId。深浅门类层级不一，靠探测最短存在的 book.json 解析：
 * nav 层(藏/部/子类)没有 book.json，第一个命中的前缀即书根。
 * 应用内导航请优先用 router state 传 bookId，免去这些探测请求。
 */
export async function resolveBookId(chapterId: string): Promise<string> {
  const parts = chapterId.split('/')
  for (let i = 2; i <= parts.length; i++) {
    const cand = parts.slice(0, i).join('/')
    try {
      await getBook(cand)
      return cand
    } catch {
      /* 该前缀是 nav 层，继续 */
    }
  }
  return parts.slice(0, 2).join('/')
}

/** 把书的 nodes 树深度优先拍平成线性正文序列(上一篇/下一篇用)。 */
export function flattenBook(nodes: BookNode[]): BookText[] {
  const out: BookText[] = []
  const walk = (ns: BookNode[]) => {
    for (const n of ns) {
      if (n.type === 'text') out.push(n)
      else walk(n.children)
    }
  }
  walk(nodes)
  return out
}

/** 把 catalog 导航树拍平成书列表(门类页先简单平铺展示)。 */
export function flattenCatalog(tree: CatalogNode[]): BookRef[] {
  const out: BookRef[] = []
  const walk = (ns: CatalogNode[]) => {
    for (const n of ns) {
      if (n.type === 'book') out.push(n)
      else walk(n.children)
    }
  }
  walk(tree)
  return out
}
