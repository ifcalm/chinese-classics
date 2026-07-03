// 内容 loader：按需 fetch dist-content 的 JSON/md，带内存缓存。
// 本地 dev 从 /content（软链到 dist-content）取；将来换 R2 只需改 BASE。
import type { Manifest, Catalog, BookDetail, BookNode, BookText, CatalogNode, BookRef } from './types'

// dev 走本地软链 /content；部署时用 VITE_CONTENT_BASE 指向 R2 公共域或 Worker /api
const BASE = import.meta.env.VITE_CONTENT_BASE ?? '/content'

/** 请求超时：连接停滞时让 Promise 快速落定，避免挂起的请求永远占住缓存
    (症状：翻页一直空白，必须刷新才恢复)。旧浏览器无 AbortSignal.timeout 则不限时。 */
const fetchTimeout = () =>
  typeof AbortSignal?.timeout === 'function' ? AbortSignal.timeout(12000) : undefined

/** 超时/断网等底层异常转为用户可读文案；业务抛出的 Error 原样保留。 */
function toFriendlyError(e: unknown, fallback: string): Error {
  if (e instanceof Error) {
    if (e.name === 'TimeoutError' || e.name === 'AbortError') return new Error('网络超时，请重试')
    if (e.name === 'TypeError') return new Error('网络异常，请检查连接后重试')
    return e
  }
  return new Error(fallback)
}

/** SPA fallback 会对不存在的路径返回 200 + index.html，须按 content-type 甄别。 */
const jsonCache = new Map<string, Promise<unknown>>()
function getJson<T>(key: string): Promise<T> {
  let p = jsonCache.get(key)
  if (!p) {
    p = fetch(`${BASE}/${key}`, { signal: fetchTimeout() })
      .then((r) => {
        const ct = r.headers.get('content-type') ?? ''
        if (!r.ok || !ct.includes('json')) throw new Error('没有找到这份内容')
        return r.json()
      })
      .catch((e) => {
        jsonCache.delete(key) // 失败不缓存，下次可重试
        throw toFriendlyError(e, '内容暂时无法加载')
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
    p = fetch(`${BASE}/${src}`, { signal: fetchTimeout() })
      .then((r) => {
        const ct = r.headers.get('content-type') ?? ''
        if (!r.ok || ct.includes('text/html')) throw new Error('没有找到这篇正文')
        return r.text()
      })
      .catch((e) => {
        textCache.delete(src)
        throw toFriendlyError(e, '正文暂时无法加载')
      })
    textCache.set(src, p)
  }
  return p
}

/** 汇总全部门类目录里的书目（书名检索用），12 个 catalog 请求、有缓存。 */
export async function getAllBooks(): Promise<Array<BookRef & { categoryName: string }>> {
  const m = await getManifest()
  const catalogs = await Promise.all(
    m.categories.map(async (c) => {
      try {
        const cat = await getCatalog(c.id)
        return flattenCatalog(cat.tree).map((b) => ({ ...b, categoryName: c.name }))
      } catch {
        return [] // 单个门类失败不拖垮整体检索
      }
    })
  )
  return catalogs.flat()
}

/** 统一取用户可读的错误文案。 */
export const errText = (e: unknown) => (e instanceof Error ? e.message : String(e))

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
