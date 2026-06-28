import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getManifest, getCatalog, flattenCatalog } from '../data/content'
import type { BookRef } from '../data/types'

export default function Category() {
  const { id = '' } = useParams()
  const [name, setName] = useState<string>()
  const [books, setBooks] = useState<BookRef[] | null>(null)
  const [err, setErr] = useState<string>()

  useEffect(() => {
    setBooks(null)
    setErr(undefined)
    getManifest().then((m) => setName(m.categories.find((c) => c.id === id)?.name))
    getCatalog(id)
      .then((c) => setBooks(flattenCatalog(c.tree)))
      .catch((e) => setErr(String(e)))
  }, [id])

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
        {books && <span className="cat-title__count">共 {books.length} 部</span>}
      </p>

      {err && <p className="empty">加载失败：{err}</p>}

      {books == null ? (
        <p className="empty">载入中…</p>
      ) : books.length === 0 ? (
        <p className="empty">该门类暂未收录书目。</p>
      ) : (
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
      )}
    </main>
  )
}
