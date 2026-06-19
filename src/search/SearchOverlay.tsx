import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { books } from '../data/books'
import { SearchIcon } from '../components/Icons'

interface Hit {
  bookId: string
  bookTitle: string
  chapterId: string
  chapterTitle: string
  snippet: string
}

// 占位检索：客户端遍历过滤。接入 R2 后改为查询预建索引（Pagefind / KV）。
function search(q: string): Hit[] {
  const query = q.trim()
  if (!query) return []
  const hits: Hit[] = []
  for (const b of books) {
    for (const c of b.chapters) {
      const haystack = `${b.title} ${b.author} ${c.title} ${c.text}`
      const at = haystack.indexOf(query)
      if (at >= 0 || b.title.includes(query)) {
        const pos = c.text.indexOf(query)
        const snippet =
          pos >= 0
            ? c.text.slice(Math.max(0, pos - 8), pos + query.length + 14)
            : c.text.slice(0, 22)
        hits.push({
          bookId: b.id,
          bookTitle: b.title,
          chapterId: c.id,
          chapterTitle: c.title,
          snippet,
        })
      }
    }
  }
  return hits.slice(0, 20)
}

export default function SearchOverlay({ onClose }: { onClose: () => void }) {
  const [q, setQ] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => inputRef.current?.focus(), [])

  const hits = useMemo(() => search(q), [q])

  const goto = (h: Hit) => {
    navigate(`/read/${h.bookId}/${h.chapterId}`)
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
            placeholder="搜原文、书名、篇章…"
            aria-label="检索"
          />
          <kbd className="search-box__kbd">Esc</kbd>
        </div>

        {q.trim() === '' ? (
          <p className="search-box__hint">输入关键词检索全文，按 Esc 关闭。</p>
        ) : hits.length === 0 ? (
          <p className="search-box__hint">没有找到「{q}」相关内容。</p>
        ) : (
          <ul className="search-box__list">
            {hits.map((h, i) => (
              <li key={i}>
                <button className="search-hit" onClick={() => goto(h)}>
                  <span className="search-hit__title">
                    {h.bookTitle} · {h.chapterTitle}
                  </span>
                  <span className="search-hit__snippet">…{h.snippet}…</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
