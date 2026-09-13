import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

// dev 时把 /content/* 直接从磁盘上的 dist-content 供给。
//
// 为什么不再用 public/content 软链（2026-09-13 换掉）：vite 会把整个 publicDir 实体拷进 dist，
// 软链一并跟进去 —— 每次 build 白删白拷 11.7 万文件 / 817MB，而 dist/content 从来没被用过
// （public/.assetsignore 把它挡在静态资产之外，线上 /content/* 由 Worker 代理 R2）。
// 实测：带软链 21.7s / dist 822MB，换成本插件后 0.78s / dist 1.6MB。
//
// 只在 serve 生效；线上与 `wrangler dev` 的 /content/* 都走 src/worker.ts 的 R2 代理，不经此处。
const CONTENT_DIR = 'dist-content'
const PREFIX = '/content/'
const MIME: Record<string, string> = {
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
}

function devContent(): Plugin {
  return {
    name: 'dev-content',
    apply: 'serve',
    configureServer(server) {
      const root = path.resolve(CONTENT_DIR)
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split('?')[0]
        if (!url?.startsWith(PREFIX)) return next()
        let rel: string
        try {
          rel = decodeURIComponent(url.slice(PREFIX.length))
        } catch {
          return next()
        }
        const file = path.resolve(root, rel)
        // 防路径穿越：解析后必须仍在 dist-content 之内
        if (file !== root && !file.startsWith(root + path.sep)) {
          res.statusCode = 403
          return res.end('forbidden')
        }
        fs.stat(file, (err, st) => {
          if (err || !st.isFile()) {
            res.statusCode = 404
            return res.end('not found')
          }
          res.setHeader('Content-Type', MIME[path.extname(file)] ?? 'application/octet-stream')
          res.setHeader('Cache-Control', 'no-cache')
          fs.createReadStream(file).pipe(res)
        })
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), devContent()],
  build: {
    // 兼容国产浏览器常见的旧 Chromium 内核(360/QQ/搜狗多为 86~94)：
    // 只降语法转译目标；运行时新 API(如 AbortSignal.timeout)在代码里已做特性检测
    target: ['chrome87', 'edge88', 'firefox78', 'safari14'],
    // 随包发布 sourcemap：线上报错堆栈直接映射回源码，便于远程定位
    sourcemap: true,
  },
})
