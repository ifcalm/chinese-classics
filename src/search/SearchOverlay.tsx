import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAllBooks } from '../data/content'
import type { BookRef } from '../data/types'
import { SearchIcon } from '../components/Icons'

type IndexedBook = BookRef & { categoryName: string }

// 书名级检索：打开浮层时汇总各门类目录(有缓存)。
// 全文检索待预建索引(Pagefind / KV)后接入，见 docs/data-architecture.md。
function search(q: string, books: IndexedBook[]): IndexedBook[] {
  const query = q.trim()
  if (!query) return []
  const hits: IndexedBook[] = []
  for (const b of books) {
    const haystack = `${b.title} ${b.author ?? ''} ${b.summary ?? ''} ${b.categoryName}`
    if (haystack.includes(query)) hits.push(b)
    if (hits.length >= 30) break
  }
  return hits
}

export default function SearchOverlay({ onClose }: { onClose: () => void }) {
  const [q, setQ] = useState('')
  const [books, setBooks] = useState<IndexedBook[] | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => inputRef.current?.focus(), [])
  useEffect(() => {
    getAllBooks().then(setBooks).catch(() => setBooks([]))
  }, [])

  const hits = useMemo(() => (books ? search(q, books) : []), [q, books])

  const goto = (b: IndexedBook) => {
    navigate(`/book/${b.id}`)
    onClose()
  }

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-box" onClick={(e) => e.stopPropagation()}>
        <div className="search-box__input">
          <SearchIcon size={17} />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜书名、作者…"
            aria-label="检索"
          />
          <kbd className="search-box__kbd">Esc</kbd>
        </div>

        {q.trim() === '' ? (
          <p className="search-box__hint">输入书名或作者检索，按 Esc 关闭。</p>
        ) : books == null ? (
          <p className="search-box__hint">正在载入书目…</p>
        ) : hits.length === 0 ? (
          <p className="search-box__hint">没有找到「{q}」相关书目。</p>
        ) : (
          <ul className="search-box__list">
            {hits.map((b) => (
              <li key={b.id}>
                <button className="search-hit" onClick={() => goto(b)}>
                  <span className="search-hit__title">{b.title}</span>
                  <span className="search-hit__snippet">
                    {b.categoryName} · {b.chapterCount} 篇
                    {b.summary ? ` · ${b.summary.slice(0, 24)}` : ''}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
