import { Link, Outlet } from 'react-router-dom'
import { isCurrentUserAdmin } from '../utils/auth'

export default function Layout() {
  const isAdmin = isCurrentUserAdmin()

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          VKR Library Recommender
        </Link>

        <nav className="nav">
          <Link to="/">Главная</Link>
          <Link to="/catalog">Каталог</Link>
          <Link to="/recommendations">Рекомендации</Link>
          <Link to="/profile">Профиль</Link>
          {isAdmin && <Link to="/admin">Админка</Link>}
        </nav>
      </header>

      <main className="page-container">
        <Outlet />
      </main>
    </div>
  )
}
