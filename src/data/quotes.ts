// 首页名句 loader：优先 Worker /api/quotes/random（D1 服务端随机），
// 本地 dev 无 Worker 或接口异常时回退 R2 quotes.json 客户端随机。
// 两路数据同源于 git 的 data/quotes.json，形状一致。
import type { Quote, QuotesFile } from './types'

const BASE = import.meta.env.VITE_CONTENT_BASE ?? '/content'

const fetchTimeout = () =>
  typeof AbortSignal?.timeout === 'function' ? AbortSignal.timeout(8000) : undefined

async function fromApi(): Promise<Quote | null> {
  try {
    const r = await fetch('/api/quotes/random', { signal: fetchTimeout() })
    const ct = r.headers.get('content-type') ?? ''
    if (!r.ok || !ct.includes('json')) return null
    const q = (await r.json()) as Quote
    return q?.text && q.chapterId ? q : null
  } catch {
    return null
  }
}

let poolPromise: Promise<Quote[]> | null = null
function getPool(): Promise<Quote[]> {
  if (!poolPromise) {
    poolPromise = fetch(`${BASE}/quotes.json`, { signal: fetchTimeout() })
      .then((r) => {
        const ct = r.headers.get('content-type') ?? ''
        if (!r.ok || !ct.includes('json')) throw new Error('no quotes')
        return r.json() as Promise<QuotesFile>
      })
      .then((d) => d.quotes ?? [])
      .catch(() => {
        poolPromise = null // 失败不缓存，下次可重试
        return []
      })
  }
  return poolPromise
}

/** 取一条随机名句；传 excludeId 避免「换一句」原地不动。取不到返回 null（区块隐藏）。 */
export async function getRandomQuote(excludeId?: string): Promise<Quote | null> {
  let last: Quote | null = null
  for (let i = 0; i < 2; i++) {
    const q = await fromApi()
    if (!q) break
    if (q.id !== excludeId) return q
    last = q
  }
  const pool = await getPool()
  const rest = pool.filter((q) => q.id !== excludeId)
  if (rest.length) return rest[Math.floor(Math.random() * rest.length)]
  return last
}
