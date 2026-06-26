import { Link, Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { isCurrentUserAdmin } from '../utils/auth'
import dvfuLogo from '../assets/logo2.png'

export default function Layout() {
  const isAdmin = isCurrentUserAdmin()
  const location = useLocation()

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <img src={dvfuLogo} alt="ДВФУ" className="brand-logo" />
          Рекомендательная система
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
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}
