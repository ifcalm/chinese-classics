import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSearch } from '../search/SearchProvider'
import { useBookSearch, type IndexedBook } from '../search/useBookSearch'
import SearchHits from '../search/SearchHits'
import { SearchIcon } from './Icons'

/** Header 内联搜索：聚焦时输入框拉长，结果下拉锚定在框下方。 */
export default function HeaderSearch() {
  const [q, setQ] = useState('')
  const [focused, setFocused] = useState(false)
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const { registerInput } = useSearch()
  const navigate = useNavigate()
  const { books, hits } = useBookSearch(q)

  // 注册给 SearchProvider，让 / 快捷键聚焦到这里
  useEffect(() => {
    registerInput(inputRef.current)
    return () => registerInput(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => setActive(0), [q])

  const goto = (b: IndexedBook) => {
    navigate(`/book/${b.id}`)
    setQ('')
    inputRef.current?.blur()
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      inputRef.current?.blur()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((i) => Math.min(i + 1, hits.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && hits[active]) {
      goto(hits[active])
    }
  }

  const showDrop = focused && q.trim() !== ''

  return (
    <div className="search-bar" role="search">
      <SearchIcon size={14} />
      <input
        ref={inputRef}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={onKeyDown}
        placeholder="搜书名、作者"
        aria-label="检索书目"
      />
      {!focused && <kbd className="search-bar__kbd">/</kbd>}

      {showDrop && (
        // mousedown 阻止默认，避免点击结果前输入框先失焦导致下拉消失
        <div className="search-drop" onMouseDown={(e) => e.preventDefault()}>
          {books == null ? (
            <p className="search-drop__hint">正在载入书目…</p>
          ) : hits.length === 0 ? (
            <p className="search-drop__hint">没有找到「{q}」相关书目。</p>
          ) : (
            <SearchHits hits={hits} activeIndex={active} onPick={goto} />
          )}
        </div>
      )}
    </div>
  )
}
