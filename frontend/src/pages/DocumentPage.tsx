import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  getDocumentById,
  addView,
  addFavorite,
  removeFavorite,
  addRating,
} from '../api/documents'
import { getSimilarDocuments } from '../api/recommendations'
import { getUserFavorites, getUserRatings } from '../api/users'
import type { Document } from '../types/document'
import DocumentCard from '../components/DocumentCard'
import { getCurrentUserId } from '../utils/auth'

type UserFavorite = {
  document_id: number
}

type UserRating = {
  document_id: number
  score: number
}

export default function DocumentPage() {
  const { id } = useParams()
  const numericId = Number(id)
  const userId = getCurrentUserId()
  const [document, setDocument] = useState<Document | null>(null)
  const [similarDocuments, setSimilarDocuments] = useState<Document[]>([])
  const [isFavorite, setIsFavorite] = useState(false)
  const [rating, setRating] = useState(5)
  const [savedRating, setSavedRating] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  const lastTrackedDocumentId = useRef<number | null>(null)

  useEffect(() => {
    if (!id || !userId || Number.isNaN(numericId)) {
      return
    }

    let cancelled = false

    const loadDocumentData = async () => {
      setLoading(true)
      try {
        const [doc, similar, favorites, ratings] = await Promise.all([
          getDocumentById(id),
          getSimilarDocuments(id),
          getUserFavorites(userId),
          getUserRatings(userId),
        ])

        if (cancelled) {
          return
        }

        setDocument(doc)
        setSimilarDocuments(similar)

        const typedFavorites = favorites as UserFavorite[]
        const typedRatings = ratings as UserRating[]

        setIsFavorite(typedFavorites.some((favorite) => favorite.document_id === numericId))

        const existingRating = typedRatings.find((item) => item.document_id === numericId)
        if (existingRating) {
          setSavedRating(existingRating.score)
          setRating(existingRating.score)
        } else {
          setSavedRating(null)
          setRating(5)
        }

        if (lastTrackedDocumentId.current !== numericId) {
          await addView(userId, numericId)
          lastTrackedDocumentId.current = numericId
        }
      } catch (err) {
        console.error(err)
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadDocumentData()

    return () => {
      cancelled = true
    }
  }, [id, numericId, userId])

  const handleToggleFavorite = async () => {
    if (!userId || !numericId) return
    try {
      if (isFavorite) {
        const res = await removeFavorite(userId, numericId)
        setMessage(res.message)
        setIsFavorite(false)
      } else {
        const res = await addFavorite(userId, numericId)
        setMessage(res.message)
        setIsFavorite(true)
      }
    } catch (err) {
      console.error(err)
      setMessage('Ошибка при обновлении избранного')
    }
  }

  const handleRate = async () => {
    if (!userId || !numericId) return
    try {
      const res = await addRating(userId, numericId, rating)
      setMessage(res.message)
      setSavedRating(rating)
    } catch (err) {
      console.error(err)
      setMessage('Ошибка при сохранении оценки')
    }
  }

  if (loading || !document) return <p>Загрузка...</p>

  return (
    <div>
      <h1>{document.title}</h1>
      <p><strong>Автор:</strong> {document.authors}</p>
      <p><strong>Год:</strong> {document.year || 'не указан'}</p>
      <p><strong>Категория:</strong> {document.category || 'не указана'}</p>
      <p><strong>Ключевые слова:</strong> {document.keywords || 'не указаны'}</p>
      <p><strong>Рубрики:</strong> {document.rubrics || 'не указаны'}</p>
      <p><strong>Издательство:</strong> {document.publisher || 'не указано'}</p>
      <p><strong>ISBN:</strong> {document.isbn || 'не указан'}</p>
      <p><strong>ББК:</strong> {document.bbk || 'не указан'}</p>
      <p><strong>УДК:</strong> {document.udk || 'не указан'}</p>
      <p><strong>Аннотация:</strong> {document.abstract || 'нет'}</p>

      {document.source_url && (
        <p className="document-source-action">
          <a className="external-library-link" href={document.source_url} target="_blank" rel="noreferrer">
            Открыть в библиотеке ДВФУ
          </a>
        </p>
      )}

      <button onClick={handleToggleFavorite}>
        {isFavorite ? 'Убрать из избранного' : 'Добавить в избранное'}
      </button>

      <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <select value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[1, 2, 3, 4, 5].map((value) => (
            <option key={value} value={value}>{value}</option>
          ))}
        </select>
        <button onClick={handleRate}>Сохранить оценку</button>
        <span>
          {savedRating !== null ? `Текущая оценка: ${savedRating}` : 'Оценка не поставлена'}
        </span>
      </div>

      {message && <div style={{ marginTop: '12px' }}>{message}</div>}

      <section style={{ marginTop: '32px' }}>
        <h2>Похожие документы</h2>
        <div className="grid">
          {similarDocuments.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      </section>
    </div>
  )
}
