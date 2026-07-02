import { Link } from 'react-router-dom'
import { SearchIcon } from './Icons'
import ThemeToggle from './ThemeToggle'
import { useSearch } from '../search/SearchProvider'

export default function Header() {
  const { open } = useSearch()
  return (
    <header className="site-header">
      <div className="page site-header__inner">
        <Link to="/" className="wordmark">
          古典文库
          <span className="wordmark__dot" aria-hidden="true" />
        </Link>
        <div className="site-header__right">
          <button className="search-pill" onClick={open} aria-label="搜索书名、作者">
            <SearchIcon size={14} />
            <span>搜书名、作者</span>
            <kbd className="search-pill__kbd">/</kbd>
          </button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
