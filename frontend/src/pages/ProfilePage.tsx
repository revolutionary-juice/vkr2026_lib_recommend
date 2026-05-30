import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getUserFavorites,
  getUserHistory,
  getUserProfile,
  getUserRatings,
  getUserSearchHistory,
} from '../api/users'
import type { User } from '../types/user'
import { clearCurrentUserId, requireCurrentUserId } from '../utils/auth'

type HistoryItem = {
  interaction_id: number
  document_id: number
  title: string
  authors?: string
  year?: number
  category?: string
  interaction_type: string
  weight: number
}

type FavoriteItem = {
  interaction_id: number
  document_id: number
  title: string
  authors?: string
  year?: number
  category?: string
}

type RatingItem = {
  rating_id: number
  title: string
  score: number
  document_id: number
}

type SearchHistoryItem = {
  id: number
  query: string
  created_at?: string
}

function formatDateTime(value?: string) {
  if (!value) {
    return 'дата не указана'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'дата не указана'
  }

  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ProfilePage() {
  const navigate = useNavigate()
  const userId = requireCurrentUserId()

  const [user, setUser] = useState<User | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [favorites, setFavorites] = useState<FavoriteItem[]>([])
  const [ratings, setRatings] = useState<RatingItem[]>([])
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])

  useEffect(() => {
    getUserProfile(userId).then(setUser)
    getUserHistory(userId).then(setHistory)
    getUserFavorites(userId).then(setFavorites)
    getUserRatings(userId).then(setRatings)
    getUserSearchHistory(userId).then(setSearchHistory)
  }, [userId])

  const viewHistory = useMemo(
    () => history.filter((item) => item.interaction_type === 'view'),
    [history]
  )

  const stats = useMemo(() => {
    const viewsCount = viewHistory.length
    const favoritesCount = favorites.length
    const ratingsCount = ratings.length
    const searchesCount = searchHistory.length
    return { viewsCount, favoritesCount, ratingsCount, searchesCount }
  }, [viewHistory, favorites, ratings, searchHistory])

  const handleLogout = () => {
    clearCurrentUserId()
    navigate('/login')
  }

  const goToDocument = (documentId: number) => {
    navigate(`/documents/${documentId}`)
  }

  return (
    <div className="profile-page">
      <h1 className="page-title">Личный кабинет</h1>

      {user && (
        <section className="profile-hero">
          <div className="profile-main-card">
            <div className="profile-avatar">{user.username?.slice(0, 1).toUpperCase()}</div>
            <div className="profile-main-info">
              <h2>{user.username}</h2>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Роль:</strong> {user.role}</p>
              <p className="profile-subtitle">Персональный кабинет читателя научной библиотеки</p>
              <button onClick={handleLogout} style={{ marginTop: '14px' }}>Выйти</button>
            </div>
          </div>

          <div className="profile-stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.viewsCount}</div>
              <div className="stat-label">Просмотров</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.favoritesCount}</div>
              <div className="stat-label">В избранном</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.ratingsCount}</div>
              <div className="stat-label">Оценок</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.searchesCount}</div>
              <div className="stat-label">Поисковых запросов</div>
            </div>
          </div>
        </section>
      )}

      <div className="profile-sections-grid">
        <section className="profile-section">
          <div className="section-header">
            <h2>История просмотров</h2>
            <span>{viewHistory.length}</span>
          </div>
          {viewHistory.length === 0 ? (
            <div className="empty-box">История пока пуста</div>
          ) : (
            <div className="profile-items-list">
              {viewHistory.map((item) => (
                <button
                  type="button"
                  className="profile-item-card profile-item-card-button"
                  key={item.interaction_id}
                  onClick={() => goToDocument(item.document_id)}
                >
                  <h3>{item.title}</h3>
                  <p><strong>Автор:</strong> {item.authors || 'не указан'}</p>
                  <p><strong>Год:</strong> {item.year || 'не указан'}</p>
                  <p><strong>Тип действия:</strong> {item.interaction_type}</p>
                  <p><strong>Вес:</strong> {item.weight}</p>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="profile-section">
          <div className="section-header">
            <h2>Избранное</h2>
            <span>{favorites.length}</span>
          </div>
          {favorites.length === 0 ? (
            <div className="empty-box">Пока нет избранных документов</div>
          ) : (
            <div className="profile-items-list">
              {favorites.map((item) => (
                <button
                  type="button"
                  className="profile-item-card profile-item-card-button"
                  key={item.interaction_id}
                  onClick={() => goToDocument(item.document_id)}
                >
                  <h3>{item.title}</h3>
                  <p><strong>Автор:</strong> {item.authors || 'не указан'}</p>
                  <p><strong>Год:</strong> {item.year || 'не указан'}</p>
                  <p><strong>Категория:</strong> {item.category || 'не указана'}</p>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="profile-section">
          <div className="section-header">
            <h2>Оценки</h2>
            <span>{ratings.length}</span>
          </div>
          {ratings.length === 0 ? (
            <div className="empty-box">Пока нет оценок</div>
          ) : (
            <div className="profile-items-list">
              {ratings.map((item) => (
                <button
                  type="button"
                  className="profile-item-card profile-item-card-button"
                  key={item.rating_id}
                  onClick={() => goToDocument(item.document_id)}
                >
                  <h3>{item.title}</h3>
                  <p><strong>Оценка:</strong> {item.score} / 5</p>
                  <p><strong>ID документа:</strong> {item.document_id}</p>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="profile-section">
          <div className="section-header">
            <h2>История поиска</h2>
            <span>{searchHistory.length}</span>
          </div>
          {searchHistory.length === 0 ? (
            <div className="empty-box">Поисковых запросов пока нет</div>
          ) : (
            <div className="profile-items-list">
              {searchHistory.map((item) => (
                <div className="profile-item-card" key={item.id}>
                  <h3>{item.query}</h3>
                  <p><strong>Дата:</strong> {formatDateTime(item.created_at)}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
