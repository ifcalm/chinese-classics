import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getBook } from '../data/content'
import type { BookDetail, BookNode } from '../data/types'

function NodeList({ nodes, bookId }: { nodes: BookNode[]; bookId: string }) {
  return (
    <ul className="toc-list">
      {nodes.map((n, i) =>
        n.type === 'collection' ? (
          <li key={i} className="toc-group">
            <span className="toc-group__title">{n.title}</span>
            <NodeList nodes={n.children} bookId={bookId} />
          </li>
        ) : (
          <li key={n.id}>
            <Link to={`/read/${n.id}`} state={{ bookId }} className="toc-item">
              {n.title}
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
  const [err, setErr] = useState<string>()

  useEffect(() => {
    setBook(null)
    setErr(undefined)
    getBook(bookId)
      .then(setBook)
      .catch((e) => setErr(String(e)))
  }, [bookId])

  const categoryId = bookId.split('/')[0]

  return (
    <main className="page">
      <nav className="crumb">
        <Link to="/" className="crumb__link">
          首页
        </Link>
        <span className="crumb__sep">/</span>
        <Link to={`/category/${categoryId}`} className="crumb__link">
          {categoryId}
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
          <NodeList nodes={book.nodes} bookId={book.id} />
        </>
      )}
    </main>
  )
}
