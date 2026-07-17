# SEO 架构（Issue #46）

原则：**SEO 不是逐页配置，而是一套从内容 JSON 派生页面元数据的规则**。
新增任何书/门类，走正常 `content:build` + `content:upload` 即自动获得
边缘渲染、元数据与 sitemap 覆盖，零额外步骤。

## 三层结构

### 1. Worker 边缘渲染（src/worker.ts + src/seo/）

SPA 对爬虫是空页面（`<div id="root">` 无内容、全站共用一份 title），
且 34k+ 篇章页无真实链接可爬。Worker 本就拦截全部请求、可直读 R2 的
内容 JSON（与 SPA 消费同一份数据），故在边缘拼出完整 HTML：

- 拦截 `GET /`、`/category/*`、`/book/*`、`/read/*`；
- 从 R2 取 manifest / catalog / book JSON / 正文 md，按 `src/seo/pages.ts`
  模板渲染：title、description、canonical、Open Graph、JSON-LD
  （WebSite/Book/Article/BreadcrumbList）、正文全文、真实 `<a>` 链接
  （目录、上一篇/下一篇）；
- 结果注入构建产物 `dist/index.html` 的 `#root`，SPA 脚本照常加载，
  React `createRoot` 首次 render 时整体替换接管交互。用户侧白赚正文首屏直出；
- 未知 ID 返回 **HTTP 404**（此前 SPA 对一切路径回 200，是软 404）；
- 渲染结果经 Cloudflare Cache API 缓存（`s-maxage=3600`）；
- **任何渲染异常回退纯 SPA shell** —— SEO 层故障不影响可用性；
- `/content/*` 原始 JSON/md 加 `X-Robots-Tag: noindex`，防与页面重复收录
  （不能用 robots.txt 屏蔽：Googlebot 渲染 SPA 时还需要 fetch 这些数据）。

### 2. sitemap 自动生成（scripts/gen-sitemap.mjs）

挂在 `content:build` 链上，从 dist-content 派生：

- `sitemap/pages.xml`：首页 + 门类页；
- `sitemap/<category>.xml`：该门类全部书目页 + 篇章页，`lastmod` 取
  book.json 的 `updatedAt`（构建状态维护的内容时间）；单片超 4 万 URL 自动分片；
- `sitemap/index.xml`：sitemap index。

产物登记进 `.files.json` 随 `content:upload` 增量上 R2；
Worker 把 `/sitemap.xml`、`/sitemap/*.xml` 映射到这些 key。
`public/robots.txt` 声明 sitemap 地址。

### 2.5 IndexNow 即时推送（挂在 content:upload 里）

`scripts/upload-r2-s3.mjs` 上传完成后，把**本次真正上传成功的 R2 key**
映射回页面 URL（`text/*.md`→`/read/*`、`book/*.json`→`/book/*`、
`catalog/*.json`→`/category/*`、`manifest.json`→`/`），POST 给
`api.indexnow.org`（Bing/Yandex 等参与引擎，Google 不支持），
新增/改动的收录延迟从天级降到小时级。推送失败只记日志，不影响上传。

- API key：`ddeed9f50cd0a63cc3e51d7b6a882666`，验证文件托管在
  `public/<key>.txt`（Worker 静态资产），与脚本内常量须一致；
- 协议单次上限 1 万 URL，脚本自动分批；正常增量远小于此；
- sitemap/`.files.json` 等非页面产物不推送。

### 3. 前端同步（派生规则与 Worker 同源）

- 标题/描述派生规则唯一事实源在 `src/seo/meta.ts`，Worker 模板与各页面
  `document.title` 同步共用，两边永不漂移；
- 阅读页翻页/目录抽屉是真实 `<Link>`（渲染为 `<a href>`），爬虫可循链发现全部篇章；
- `isVerse` / 正文块级渲染规则在 `src/seo/render.ts`，Reader 与边缘渲染共用判定。

## 派生规则（即「SEO 数据模型」）

| 页面 | title | description |
|---|---|---|
| 首页 | 古典文库 · Chinese Classics | 站点固定文案 |
| 门类 | `<门类名> \| 古典文库` | `<门类名>典籍 N 部…` |
| 书目 | `<书名>目录 \| 古典文库` | summary + `《书名》全文在线阅读，共 N 篇…` |
| 阅读 | `<篇名> · <书名> \| 古典文库`（篇名剥「书名-」前缀） | 正文剥标记后前 110 字 |

canonical 域名：`https://www.chinese-classics.org`。

## 注意事项

- `public/content` 软链 vite 会实体拷进 dist（374MB/34k 文件），
  `public/.assetsignore` 已把它排除出 Worker 静态资产（2 万文件上限，
  且线上 `/content/*` 由 Worker 代理 R2，轮不到 ASSETS）；
- 模板改动只需 `npm run deploy`，不必重传内容；内容改动只需
  `content:build` + `content:upload`，不必重新部署 Worker；
- 边缘 HTML 缓存 1 小时：内容更新后最长 1 小时可见旧页，可接受；
  如需立即生效可在 Cloudflare 控制台 purge cache；
- 本地无法 `wrangler dev`（沙箱下 spawn EBADF），端到端验证用
  `wrangler deploy --dry-run --outdir` 打 bundle 后在 Node 里驱动
  （ASSETS←dist、BOOKS←dist-content 打桩），见会话记录。
