import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCategory } from '../data/categories'
import { getBooksByCategory } from '../data/books'

export default function Category() {
  const { id = '' } = useParams()
  const category = getCategory(id)
  const allBooks = useMemo(() => getBooksByCategory(id), [id])

  const dynasties = useMemo(
    () => Array.from(new Set(allBooks.map((b) => b.dynasty))),
    [allBooks]
  )
  const [filter, setFilter] = useState<string>('全部')

  const books = filter === '全部' ? allBooks : allBooks.filter((b) => b.dynasty === filter)

  return (
    <main className="page">
      <nav className="crumb">
        <Link to="/" className="crumb__link">
          首页
        </Link>
        <span className="crumb__sep">/</span>
        <span>{category?.name ?? '未知门类'}</span>
      </nav>

      <h1 className="cat-title">{category?.name ?? '未知门类'}</h1>
      <p className="cat-title__sub">
        {category?.subtitle}
        {allBooks.length > 0 && <span className="cat-title__count"> · 共 {allBooks.length} 部</span>}
      </p>

      {dynasties.length > 1 && (
        <div className="pills">
          {['全部', ...dynasties].map((d) => (
            <button
              key={d}
              className={`pill ${filter === d ? 'pill--active' : ''}`}
              onClick={() => setFilter(d)}
            >
              {d}
            </button>
          ))}
        </div>
      )}

      {books.length === 0 ? (
        <p className="empty">该门类暂未收录书目。</p>
      ) : (
        <div className="book-grid">
          {books.map((b) => (
            <Link key={b.id} to={`/read/${b.id}/${b.chapters[0]?.id ?? '1'}`} className="book-card">
              <span className="book-card__bottom">
                <span className="book-card__title">{b.title}</span>
                <span className="book-card__meta">
                  {b.author} · {b.dynasty}
                </span>
              </span>
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
