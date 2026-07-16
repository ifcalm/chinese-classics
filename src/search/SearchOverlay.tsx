import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBookSearch, type IndexedBook } from './useBookSearch'
import SearchHits from './SearchHits'
import { SearchIcon } from '../components/Icons'

/** 居中检索浮层：阅读页(无 Header)按 / 唤起时的兜底入口。 */
export default function SearchOverlay({ onClose }: { onClose: () => void }) {
  const [q, setQ] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const { books, hits } = useBookSearch(q)

  // 块体：隐式返回会把 focus() 的返回值当清理函数(见 Reader 同注)
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

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
          <SearchHits hits={hits} onPick={goto} />
        )}
      </div>
    </div>
  )
}
