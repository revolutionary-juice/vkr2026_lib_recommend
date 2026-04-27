import { useEffect, useState } from 'react'
import { getHybridRecommendations } from '../api/recommendations'
import DocumentCard from '../components/DocumentCard'
import type { Document } from '../types/document'
import { requireCurrentUserId } from '../utils/auth'

export default function RecommendationsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const userId = requireCurrentUserId()

  useEffect(() => {
    getHybridRecommendations(userId).then(setDocuments)
  }, [userId])

  return (
    <div className="content-stack">
      <h1 className="page-title">Рекомендации</h1>
      <section className="content-section">
        <div className="section-head">
          <h2>Персональная подборка</h2>
          <p>Сформировано по вашим просмотрам, избранному и оценкам</p>
        </div>
        <div className="grid">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      </section>
    </div>
  )
}
