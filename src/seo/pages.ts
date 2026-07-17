// Worker 边缘渲染的页面模板：纯函数，输入内容 JSON、输出 head 元数据 + #root 内 HTML。
// 四类路由(首页/门类/书目/阅读)各一个，规则派生自 meta.ts，不依赖任何运行时环境。

import type { BookDetail, BookNode, BookText, CategoryMeta, CatalogNode, Manifest } from '../data/types'
import {
  SITE_NAME, SITE_TITLE, SITE_URL, SITE_DESC,
  chapterDisplayTitle, chapterPageTitle, bookPageTitle, categoryPageTitle,
  descriptionFromText, bookDescription, categoryDescription,
} from './meta'
import { escapeHtml, isVerse, mdToHtml } from './render'

export interface PageMeta {
  title: string
  description: string
  /** canonical 路径(不含域名) */
  path: string
  ogType: 'website' | 'article'
  jsonLd: object[]
  /** 注入 <div id="root"> 的 HTML，React 挂载时整体替换 */
  body: string
  /** 缺省 200；404 页置 404 */
  status?: 404
}

const e = escapeHtml

function breadcrumbLd(items: Array<{ name: string; path?: string }>): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      ...(it.path ? { item: SITE_URL + it.path } : {}),
    })),
  }
}

// ── 首页 ──────────────────────────────────────────────
export function renderHome(manifest: Manifest): PageMeta {
  const total = manifest.categories.reduce((s, c) => s + c.bookCount, 0)
  const cards = manifest.categories
    .map(
      (c) => `<a class="cat-card" href="/category/${e(c.id)}"><span class="cat-card__bottom"><span class="cat-card__name">${e(c.name)}</span><span class="cat-card__sub">${e(c.subtitle ?? `${c.bookCount} 部`)}</span></span></a>`
    )
    .join('\n')
  return {
    title: SITE_TITLE,
    description: SITE_DESC,
    path: '/',
    ogType: 'website',
    jsonLd: [
      {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: SITE_NAME,
        url: SITE_URL,
        description: SITE_DESC,
        inLanguage: 'zh',
      },
    ],
    body: `<main class="page">
<section class="hero"><h1 class="hero__title">读经典，<span class="accent">不必正襟危坐。</span></h1>
<p class="hero__sub">${manifest.categories.length} 门类 · ${total} 部典籍 · 书名可搜</p></section>
<section class="bento" aria-label="门类导航">
${cards}
</section></main>`,
  }
}

// ── 门类页 ────────────────────────────────────────────
function catalogHtml(nodes: CatalogNode[], depth: number): string {
  const books = nodes.filter((n) => n.type === 'book')
  const groups = nodes.filter((n) => n.type === 'collection')
  const grid = books.length
    ? `<div class="book-grid">${books
        .map(
          (b) => `<a class="book-card" href="/book/${e(b.id)}"><span class="book-card__bottom"><span class="book-card__title">${e(b.title)}</span><span class="book-card__meta">${b.chapterCount} 篇</span></span></a>`
        )
        .join('')}</div>`
    : ''
  const sections = groups
    .map(
      (g) => `<section class="book-group">${depth === 0 ? `<h2 class="book-group__title">${e(g.title)}</h2>` : `<h3 class="book-group__subtitle">${e(g.title)}</h3>`}${catalogHtml(g.children, depth + 1)}</section>`
    )
    .join('\n')
  return grid + sections
}

export function renderCategory(cat: CategoryMeta, tree: CatalogNode[]): PageMeta {
  const path = `/category/${cat.id}`
  return {
    title: categoryPageTitle(cat.name),
    description: categoryDescription(cat.name, cat.bookCount),
    path,
    ogType: 'website',
    jsonLd: [breadcrumbLd([{ name: '首页', path: '/' }, { name: cat.name }])],
    body: `<main class="page">
<nav class="crumb"><a class="crumb__link" href="/">首页</a><span class="crumb__sep">/</span><span>${e(cat.name)}</span></nav>
<h1 class="cat-title">${e(cat.name)}</h1>
<p class="cat-title__sub"><span class="cat-title__count">共 ${cat.bookCount} 部</span></p>
${catalogHtml(tree, 0)}</main>`,
  }
}

// ── 书目页 ────────────────────────────────────────────
function tocHtml(bookTitle: string, nodes: BookNode[]): string {
  // 卷号 = 全书连续序数(DFS 与拍平阅读顺序一致)；篇名剥「书名-」前缀。与 Book.tsx 同款
  let n = 0
  const t = (s: string) => e(chapterDisplayTitle(bookTitle, s))
  const walk = (ns: BookNode[]): string =>
    `<ul class="toc-list">${ns
      .map((node) =>
        node.type === 'collection'
          ? `<li class="toc-group"><span class="toc-group__title">${t(node.title)}</span>${walk(node.children)}</li>`
          : `<li><a class="toc-item" href="/read/${e(node.id)}"><span class="toc-item__num" aria-hidden="true">${++n}</span>${t(node.title)}</a></li>`
      )
      .join('')}</ul>`
  return walk(nodes)
}

export function renderBookPage(book: BookDetail, catName: string, chapterCount: number): PageMeta {
  const categoryId = book.id.split('/')[0]
  const path = `/book/${book.id}`
  return {
    title: bookPageTitle(book.title),
    description: bookDescription(book.title, book.summary, chapterCount),
    path,
    ogType: 'website',
    jsonLd: [
      {
        '@context': 'https://schema.org',
        '@type': 'Book',
        name: book.title,
        ...(book.summary ? { description: book.summary } : {}),
        ...(book.author ? { author: { '@type': 'Person', name: book.author } } : {}),
        url: SITE_URL + path,
        inLanguage: 'zh',
        dateModified: book.updatedAt,
      },
      breadcrumbLd([
        { name: '首页', path: '/' },
        { name: catName, path: `/category/${categoryId}` },
        { name: book.title },
      ]),
    ],
    body: `<main class="page">
<nav class="crumb"><a class="crumb__link" href="/">首页</a><span class="crumb__sep">/</span><a class="crumb__link" href="/category/${e(categoryId)}">${e(catName)}</a><span class="crumb__sep">/</span><span>${e(book.title)}</span></nav>
<h1 class="cat-title">${e(book.title)}</h1>
${book.summary ? `<p class="cat-title__sub">${e(book.summary)}</p>` : ''}
${tocHtml(book.title, book.nodes)}</main>`,
  }
}

// ── 阅读页 ────────────────────────────────────────────
export function renderChapterPage(
  book: BookDetail,
  chapter: BookText,
  prev: BookText | undefined,
  next: BookText | undefined,
  text: string
): PageMeta {
  const path = `/read/${chapter.id}`
  const shortTitle = chapterDisplayTitle(book.title, chapter.title)
  const verse = isVerse(text)
  const content = verse ? `<div class="reader__verse">${mdToHtml(text)}</div>` : mdToHtml(text)
  const navLink = (c: BookText, arrow: 'prev' | 'next') =>
    `<a class="reader__nav-btn" rel="${arrow}" href="/read/${e(c.id)}">${arrow === 'prev' ? `← ${e(chapterDisplayTitle(book.title, c.title))}` : `${e(chapterDisplayTitle(book.title, c.title))} →`}</a>`
  return {
    title: chapterPageTitle(book.title, chapter.title),
    description: descriptionFromText(text) || `《${book.title}》${shortTitle}，全文在线阅读。`,
    path,
    ogType: 'article',
    jsonLd: [
      {
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: `${book.title}·${shortTitle}`,
        isPartOf: { '@type': 'Book', name: book.title, url: `${SITE_URL}/book/${book.id}` },
        url: SITE_URL + path,
        inLanguage: 'zh',
        dateModified: book.updatedAt,
      },
      breadcrumbLd([
        { name: '首页', path: '/' },
        { name: book.title, path: `/book/${book.id}` },
        { name: shortTitle },
      ]),
    ],
    body: `<div class="reader">
<div class="page reader__bar"><a class="reader__back" href="/book/${e(book.id)}" aria-label="返回目录">‹</a><span class="reader__crumb">${e(book.title)} · ${e(shortTitle)}</span><a class="reader__toc-btn" href="/book/${e(book.id)}">目录</a></div>
<article class="page reader__body">
<h1 class="reader__chapter">${e(shortTitle)}</h1>
<div class="reader__rule" aria-hidden="true"></div>
<div class="reader__flow${verse ? ' reader__flow--verse' : ''}">
${content}
</div>
<nav class="reader__nav">${prev ? navLink(prev, 'prev') : '<span></span>'}${next ? navLink(next, 'next') : '<span></span>'}</nav>
</article></div>`,
  }
}

// ── 404 ──────────────────────────────────────────────
export function renderNotFound(path: string): PageMeta {
  return {
    title: `未找到 | ${SITE_NAME}`,
    description: SITE_DESC,
    path,
    ogType: 'website',
    jsonLd: [],
    status: 404,
    body: `<main class="page"><p class="empty">没有找到这个页面，<a class="accent" href="/">返回首页</a>。</p></main>`,
  }
}
