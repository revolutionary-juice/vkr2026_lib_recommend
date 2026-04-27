import { useEffect, useState } from 'react'
import { getPopularDocuments, getRecentDocuments } from '../api/documents'
import type { Document } from '../types/document'
import DocumentCard from '../components/DocumentCard'

export default function HomePage() {
  const [popular, setPopular] = useState<Document[]>([])
  const [recent, setRecent] = useState<Document[]>([])

  useEffect(() => {
    getPopularDocuments().then(setPopular)
    getRecentDocuments().then(setRecent)
  }, [])

  return (
    <div className="content-stack">
      <h1 className="page-title">Главная</h1>

      <section className="content-section">
        <div className="section-head">
          <h2>Популярные документы</h2>
          <p>Подборка наиболее востребованных материалов</p>
        </div>
        <div className="grid">
          {popular.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      </section>

      <section className="content-section">
        <div className="section-head">
          <h2>Новые документы</h2>
          <p>Последние добавления в каталог</p>
        </div>
        <div className="grid">
          {recent.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      </section>
    </div>
  )
}
