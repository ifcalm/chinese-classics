import { Route, Routes } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import Category from './pages/Category'
import Reader from './pages/Reader'
import { SearchProvider } from './search/SearchProvider'
import './styles/app.css'

export default function App() {
  return (
    <SearchProvider>
      <Routes>
        {/* 阅读页是独立沉浸布局，不带全局 Header */}
        <Route path="/read/:bookId/:chapterId" element={<Reader />} />
        <Route
          path="*"
          element={
            <>
              <Header />
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/category/:id" element={<Category />} />
              </Routes>
            </>
          }
        />
      </Routes>
    </SearchProvider>
  )
}
