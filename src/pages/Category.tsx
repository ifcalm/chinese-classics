import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { errText, getManifest, getCatalog, flattenCatalog } from '../data/content'
import type { BookRef, CatalogNode } from '../data/types'
import { categoryPageTitle, SITE_TITLE } from '../seo/meta'

function BookGrid({ books }: { books: BookRef[] }) {
  if (books.length === 0) return null
  return (
    <div className="book-grid">
      {books.map((b) => (
        <Link key={b.id} to={`/book/${b.id}`} className="book-card">
          <span className="book-card__bottom">
            <span className="book-card__title">{b.title}</span>
            <span className="book-card__meta">{b.chapterCount} 篇</span>
          </span>
        </Link>
      ))}
    </div>
  )
}

/** 按目录树分组渲染：同层书目铺网格，藏/部层出标题递归；depth 控制标题层级。 */
function TreeSection({ nodes, depth }: { nodes: CatalogNode[]; depth: number }) {
  const books = nodes.filter((n): n is BookRef => n.type === 'book')
  const groups = nodes.filter((n) => n.type === 'collection')
  return (
    <>
      <BookGrid books={books} />
      {groups.map((g) => (
        <section key={g.title} id={depth === 0 ? `g-${g.title}` : undefined} className="book-group">
          {depth === 0 ? (
            <h2 className="book-group__title">{g.title}</h2>
          ) : (
            <h3 className="book-group__subtitle">{g.title}</h3>
          )}
          <TreeSection nodes={g.children} depth={depth + 1} />
        </section>
      ))}
    </>
  )
}

export default function Category() {
  const { id = '' } = useParams()
  const [name, setName] = useState<string>()
  const [tree, setTree] = useState<CatalogNode[] | null>(null)
  const [err, setErr] = useState<string>()

  useEffect(() => {
    setTree(null)
    setErr(undefined)
    getManifest()
      .then((m) => setName(m.categories.find((c) => c.id === id)?.name))
      .catch(() => {})
    getCatalog(id)
      .then((c) => setTree(c.tree))
      .catch((e) => setErr(errText(e)))
  }, [id])

  // 客户端导航时同步标题，派生规则与 Worker 边缘渲染同源(seo/meta)
  useEffect(() => {
    document.title = name ? categoryPageTitle(name) : SITE_TITLE
  }, [name])

  const bookCount = tree ? flattenCatalog(tree).length : 0
  const topGroups = tree?.filter((n) => n.type === 'collection') ?? []

  return (
    <main className="page">
      <nav className="crumb">
        <Link to="/" className="crumb__link">
          首页
        </Link>
        <span className="crumb__sep">/</span>
        <span>{name ?? '未知门类'}</span>
      </nav>

      <h1 className="cat-title">{name ?? '门类'}</h1>
      <p className="cat-title__sub">
        {tree && <span className="cat-title__count">共 {bookCount} 部</span>}
      </p>

      {topGroups.length > 1 && (
        <nav className="pills" aria-label="分部导航">
          {topGroups.map((g) => (
            <a key={g.title} className="pill" href={`#g-${g.title}`}>
              {g.title}
            </a>
          ))}
        </nav>
      )}

      {err && <p className="empty">加载失败：{err}</p>}

      {tree == null ? (
        !err && <p className="empty">载入中…</p>
      ) : bookCount === 0 ? (
        <p className="empty">该门类暂未收录书目。</p>
      ) : (
        <TreeSection nodes={tree} depth={0} />
      )}
    </main>
  )
}
