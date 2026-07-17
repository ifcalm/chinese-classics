import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { errText, flattenBook, getBook, getManifest } from '../data/content'
import type { BookDetail, BookNode } from '../data/types'
import { bookPageTitle, chapterDisplayTitle, SITE_TITLE } from '../seo/meta'

/** num：chapterId → 全书连续序数(跨分组连贯，与拍平阅读顺序一致)，目录里的路标。
    篇名剥「书名-」前缀(与阅读页标题同规则)，书名页头已示，不必每项重复。 */
function NodeList({ nodes, book, num }: { nodes: BookNode[]; book: BookDetail; num: Map<string, number> }) {
  return (
    <ul className="toc-list">
      {nodes.map((n, i) =>
        n.type === 'collection' ? (
          <li key={i} className="toc-group">
            <span className="toc-group__title">{chapterDisplayTitle(book.title, n.title)}</span>
            <NodeList nodes={n.children} book={book} num={num} />
          </li>
        ) : (
          <li key={n.id}>
            <Link to={`/read/${n.id}`} state={{ bookId: book.id }} className="toc-item">
              <span className="toc-item__num" aria-hidden="true">{num.get(n.id)}</span>
              {chapterDisplayTitle(book.title, n.title)}
            </Link>
          </li>
        )
      )}
    </ul>
  )
}

export default function Book() {
  const { '*': bookId = '' } = useParams()
  const [book, setBook] = useState<BookDetail | null>(null)
  const [catName, setCatName] = useState<string>()
  const [err, setErr] = useState<string>()

  const categoryId = bookId.split('/')[0]

  useEffect(() => {
    setBook(null)
    setErr(undefined)
    getBook(bookId)
      .then(setBook)
      .catch((e) => setErr(errText(e)))
    getManifest()
      .then((m) => setCatName(m.categories.find((c) => c.id === categoryId)?.name))
      .catch(() => {})
  }, [bookId, categoryId])

  // 客户端导航时同步标题，派生规则与 Worker 边缘渲染同源(seo/meta)
  useEffect(() => {
    document.title = book ? bookPageTitle(book.title) : SITE_TITLE
  }, [book])

  return (
    <main className="page">
      <nav className="crumb">
        <Link to="/" className="crumb__link">
          首页
        </Link>
        <span className="crumb__sep">/</span>
        <Link to={`/category/${categoryId}`} className="crumb__link">
          {catName ?? categoryId}
        </Link>
        <span className="crumb__sep">/</span>
        <span>{book?.title ?? '…'}</span>
      </nav>

      {err && <p className="empty">加载失败：{err}</p>}
      {book == null ? (
        !err && <p className="empty">载入中…</p>
      ) : (
        <>
          <h1 className="cat-title">{book.title}</h1>
          {book.summary && <p className="cat-title__sub">{book.summary}</p>}
          <NodeList
            nodes={book.nodes}
            book={book}
            num={new Map(flattenBook(book.nodes).map((c, i) => [c.id, i + 1]))}
          />
        </>
      )}
    </main>
  )
}
