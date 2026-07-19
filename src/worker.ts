// Cloudflare Worker：
//  1. /content/* 代理到 R2 桶（同源免 CORS；标 noindex 防原始 JSON/md 被收录）
//  2. /sitemap.xml、/sitemap/*.xml 从 R2 取（content:build 产物）
//  3. 首页/门类/书目/阅读四类路由做边缘渲染：用与 SPA 同一份 R2 数据拼出
//     完整 HTML（title/description/canonical/JSON-LD/正文/真实链接）注入 #root，
//     爬虫拿到全文，用户白赚首屏直出；React 挂载后整体替换接管交互。
//     新增内容走正常 content:build + 上传即自动覆盖，无需任何逐篇配置。
//  4. 未知 ID 返回真 404（此前 SPA 对一切路径回 200，是软 404）。
//  渲染出错时回退到纯 SPA shell —— SEO 增强绝不能把站点打挂。

import type { BookDetail, BookText, Catalog, Manifest } from './data/types'
import { SITE_URL } from './seo/meta'
import { escapeHtml } from './seo/render'
import {
  renderHome, renderCategory, renderBookPage, renderChapterPage, renderNotFound,
  type PageMeta,
} from './seo/pages'

interface R2Object {
  body: ReadableStream
  httpEtag: string
  writeHttpMetadata(headers: Headers): void
}
interface D1PreparedStatement {
  first<T = unknown>(): Promise<T | null>
}
interface Env {
  ASSETS: { fetch(req: Request): Promise<Response> }
  BOOKS: { get(key: string): Promise<R2Object | null> }
  /** 名句库 D1。可缺省：未绑定或查询失败时回退 R2 quotes.json。 */
  QUOTES_DB?: { prepare(query: string): D1PreparedStatement }
}
interface Ctx {
  waitUntil(p: Promise<unknown>): void
}

const PREFIX = '/content/'
const edgeCache = () => (caches as unknown as { default: Cache }).default

// ── R2 数据读取（与 SPA 消费同一套 JSON/md）──────────────
async function r2Text(env: Env, key: string): Promise<string | null> {
  const obj = await env.BOOKS.get(key)
  if (!obj) return null
  return new Response(obj.body).text()
}
async function r2Json<T>(env: Env, key: string): Promise<T | null> {
  const s = await r2Text(env, key)
  if (s == null) return null
  try {
    return JSON.parse(s) as T
  } catch {
    return null
  }
}

/** chapterId → 所属书。与前端 resolveBookId 同策略：由浅入深探测第一个存在的 book.json。 */
async function resolveBook(env: Env, chapterId: string): Promise<BookDetail | null> {
  const parts = chapterId.split('/')
  // i <= length：单文件书的章节 id 即书 id 本身，须探测全路径（与前端 resolveBookId 一致，曾差一个等号致全站单文件书 /read 404）
  for (let i = 2; i <= parts.length; i++) {
    const book = await r2Json<BookDetail>(env, `book/${parts.slice(0, i).join('/')}.json`)
    if (book) return book
  }
  return null
}

function flattenBook(nodes: BookDetail['nodes']): BookText[] {
  const out: BookText[] = []
  const walk = (ns: BookDetail['nodes']) => {
    for (const n of ns) {
      if (n.type === 'text') out.push(n)
      else walk(n.children)
    }
  }
  walk(nodes)
  return out
}

// ── SPA shell：从静态资源取构建后的 index.html 作注入模板 ──
let shellPromise: Promise<string> | null = null
function getShell(env: Env, origin: string): Promise<string> {
  if (!shellPromise) {
    shellPromise = env.ASSETS.fetch(new Request(`${origin}/index.html`)).then((r) => {
      if (!r.ok) {
        shellPromise = null
        throw new Error(`shell ${r.status}`)
      }
      return r.text()
    })
  }
  return shellPromise
}

/** 把渲染结果注入 shell：换 title/description，补 canonical/og/JSON-LD，填 #root。 */
function inject(shell: string, m: PageMeta): string {
  const canonical = SITE_URL + m.path
  const head = [
    `<link rel="canonical" href="${escapeHtml(canonical)}" />`,
    `<meta property="og:title" content="${escapeHtml(m.title)}" />`,
    `<meta property="og:description" content="${escapeHtml(m.description)}" />`,
    `<meta property="og:type" content="${m.ogType}" />`,
    `<meta property="og:url" content="${escapeHtml(canonical)}" />`,
    `<meta property="og:site_name" content="古典文库" />`,
    `<meta property="og:locale" content="zh_CN" />`,
    ...m.jsonLd.map(
      (o) => `<script type="application/ld+json">${JSON.stringify(o).replace(/</g, '\\u003c')}</script>`
    ),
  ].join('\n    ')
  return shell
    .replace(/<title>[^<]*<\/title>/, () => `<title>${escapeHtml(m.title)}</title>`)
    .replace(/<meta name="description" content="[^"]*" \/>/, () => `<meta name="description" content="${escapeHtml(m.description)}" />`)
    .replace('</head>', `  ${head}\n  </head>`)
    .replace('<div id="root"></div>', () => `<div id="root">${m.body}</div>`)
}

// ── 路由渲染 ──────────────────────────────────────────
async function renderRoute(env: Env, pathname: string): Promise<PageMeta | null> {
  if (pathname === '/') {
    const manifest = await r2Json<Manifest>(env, 'manifest.json')
    return manifest ? renderHome(manifest) : null
  }

  const m = /^\/(category|book|read)\/(.+)$/.exec(pathname)
  if (!m) return null
  const [, kind, rest] = m
  const id = decodeURIComponent(rest).replace(/\/+$/, '')

  if (kind === 'category') {
    const [manifest, catalog] = await Promise.all([
      r2Json<Manifest>(env, 'manifest.json'),
      r2Json<Catalog>(env, `catalog/${id}.json`),
    ])
    const cat = manifest?.categories.find((c) => c.id === id)
    if (!cat || !catalog) return renderNotFound(pathname)
    return renderCategory(cat, catalog.tree)
  }

  if (kind === 'book') {
    const book = await r2Json<BookDetail>(env, `book/${id}.json`)
    if (!book) return renderNotFound(pathname)
    const manifest = await r2Json<Manifest>(env, 'manifest.json')
    const catName = manifest?.categories.find((c) => c.id === id.split('/')[0])?.name ?? id.split('/')[0]
    return renderBookPage(book, catName, flattenBook(book.nodes).length)
  }

  // read
  const book = await resolveBook(env, id)
  if (!book) return renderNotFound(pathname)
  const flat = flattenBook(book.nodes)
  const idx = flat.findIndex((c) => c.id === id)
  if (idx < 0) return renderNotFound(pathname)
  const chapter = flat[idx]
  const text = await r2Text(env, chapter.src)
  if (text == null) return renderNotFound(pathname)
  return renderChapterPage(book, chapter, flat[idx - 1], flat[idx + 1], text)
}

/** 随机名句：D1 主（服务端 RANDOM()），R2 quotes.json 兜底。两路数据同源于
    git 的 data/quotes.json，形状一致（chapterId 驼峰）。响应不缓存——随机即卖点。 */
async function randomQuote(env: Env): Promise<Response> {
  let q: unknown = null
  try {
    q = await env.QUOTES_DB
      ?.prepare('SELECT id, text, source, chapter_id AS chapterId FROM quotes ORDER BY RANDOM() LIMIT 1')
      .first()
  } catch {
    // D1 故障不致命，落 R2 兜底
  }
  if (!q) {
    const data = await r2Json<{ quotes?: unknown[] }>(env, 'quotes.json')
    const list = data?.quotes ?? []
    if (list.length) q = list[Math.floor(Math.random() * list.length)]
  }
  if (!q) return new Response('Not found', { status: 404 })
  return new Response(JSON.stringify(q), {
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-robots-tag': 'noindex',
    },
  })
}

const isDocRoute = (p: string) => p === '/' || /^\/(category|book|read)\//.test(p)

export default {
  async fetch(req: Request, env: Env, ctx: Ctx): Promise<Response> {
    const url = new URL(req.url)

    // 裸域 301 归一到 www：canonical/sitemap 都以 www 为准，双入口 200 会摊薄权重
    if (url.hostname === 'chinese-classics.org') {
      url.hostname = 'www.chinese-classics.org'
      return Response.redirect(url.toString(), 301)
    }

    // 前端错误上报：ErrorBoundary 兜底时 POST 错误报告，console.error 落 Workers Logs。
    // 公开端点，只收同源小报文：截断到 8KB，防滥用；响应恒 204 不回显任何信息。
    if (url.pathname === '/api/err' && req.method === 'POST') {
      try {
        const body = (await req.text()).slice(0, 8192)
        console.error('[client-error]', body)
      } catch {
        /* 报文读取失败也不影响响应 */
      }
      return new Response(null, { status: 204 })
    }

    // 首页随机名句
    if (url.pathname === '/api/quotes/random' && req.method === 'GET') {
      return randomQuote(env)
    }

    // R2 内容代理（原始数据，不参与收录）
    if (url.pathname.startsWith(PREFIX)) {
      const key = decodeURIComponent(url.pathname.slice(PREFIX.length))
      const obj = await env.BOOKS.get(key)
      if (!obj) return new Response('Not found', { status: 404 })
      const headers = new Headers()
      obj.writeHttpMetadata(headers)
      headers.set('etag', obj.httpEtag)
      headers.set('cache-control', 'public, max-age=300')
      headers.set('x-robots-tag', 'noindex')
      if (!headers.has('content-type')) {
        if (key.endsWith('.json')) headers.set('content-type', 'application/json; charset=utf-8')
        else if (key.endsWith('.md')) headers.set('content-type', 'text/markdown; charset=utf-8')
      }
      return new Response(obj.body, { headers })
    }

    // sitemap（content:build 生成并随内容上传 R2）
    const smKey =
      url.pathname === '/sitemap.xml'
        ? 'sitemap/index.xml'
        : /^\/sitemap\/[\w-]+\.xml$/.test(url.pathname)
          ? url.pathname.slice(1)
          : null
    if (smKey) {
      const xml = await r2Text(env, smKey)
      if (xml == null) return new Response('Not found', { status: 404 })
      return new Response(xml, {
        headers: { 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600' },
      })
    }

    // 边缘渲染。任何异常回退纯 shell，SEO 层的故障不影响可用性。
    if (req.method === 'GET' && isDocRoute(url.pathname)) {
      try {
        const cache = edgeCache()
        const hit = await cache.match(req)
        if (hit) return hit
        const page = await renderRoute(env, url.pathname)
        if (page) {
          const shell = await getShell(env, url.origin)
          const notFound = page.status === 404
          const resp = new Response(inject(shell, page), {
            status: notFound ? 404 : 200,
            headers: {
              'content-type': 'text/html; charset=utf-8',
              'cache-control': notFound ? 'no-store' : 'public, max-age=300, s-maxage=3600',
            },
          })
          if (!notFound) ctx.waitUntil(cache.put(req, resp.clone()))
          return resp
        }
      } catch {
        // 渲染失败 → SPA shell 兜底
      }
    }

    return env.ASSETS.fetch(req)
  },
}
