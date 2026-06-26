import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loginUser } from '../api/auth'
import { getCurrentUser, setCurrentUser } from '../utils/auth'

export default function LoginPage() {
  const navigate = useNavigate()

  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const existingUser = getCurrentUser()
    if (existingUser !== null) {
      navigate(existingUser.role === 'admin' ? '/admin' : '/')
    }
  }, [navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      setLoading(true)
      const user = await loginUser(identifier, password)
      setCurrentUser(user)
      navigate(user.role === 'admin' ? '/admin' : '/')
    } catch (err: any) {
      console.error(err)
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Неверный логин или пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Вход</h1>
        <p className="auth-subtitle">Войдите в систему библиотеки.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Логин или email
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="Введите логин или email"
              required
            />
          </label>

          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
              required
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <div style={{ marginTop: '18px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Link to="/register" className="button-link">
            Нет аккаунта? Регистрация
          </Link>
        </div>

        {error && <div className="auth-message error">{error}</div>}
      </div>
    </div>
  )
}
