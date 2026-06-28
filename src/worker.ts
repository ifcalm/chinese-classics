// Cloudflare Worker：托管 SPA 静态资源，并把 /content/* 代理到 R2 桶（同源，免 CORS）。
// 应用通过 fetch('/content/manifest.json' | '/content/book/..json' | '/content/text/..md') 取数据。

interface Env {
  ASSETS: { fetch(req: Request): Promise<Response> }
  BOOKS: {
    get(key: string): Promise<{
      body: ReadableStream
      httpEtag: string
      writeHttpMetadata(headers: Headers): void
    } | null>
  }
}

const PREFIX = '/content/'

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url)
    if (url.pathname.startsWith(PREFIX)) {
      const key = decodeURIComponent(url.pathname.slice(PREFIX.length))
      const obj = await env.BOOKS.get(key)
      if (!obj) return new Response('Not found', { status: 404 })
      const headers = new Headers()
      obj.writeHttpMetadata(headers)
      headers.set('etag', obj.httpEtag)
      headers.set('cache-control', 'public, max-age=300')
      if (!headers.has('content-type')) {
        if (key.endsWith('.json')) headers.set('content-type', 'application/json; charset=utf-8')
        else if (key.endsWith('.md')) headers.set('content-type', 'text/markdown; charset=utf-8')
      }
      return new Response(obj.body, { headers })
    }
    return env.ASSETS.fetch(req)
  },
}
