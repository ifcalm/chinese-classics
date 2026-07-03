import { Link } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'
import HeaderSearch from './HeaderSearch'

export default function Header() {
  return (
    <header className="site-header">
      <div className="page site-header__inner">
        <Link to="/" className="wordmark">
          古典文库
          <span className="wordmark__dot" aria-hidden="true" />
        </Link>
        <div className="site-header__right">
          <HeaderSearch />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
