import { useEffect, useState } from 'react'
import { getDocuments } from '../api/documents'
import { api } from '../api/client'
import SearchBar from '../components/SearchBar'
import DocumentCard from '../components/DocumentCard'
import { getCurrentUserId } from '../utils/auth'
import type { Document } from '../types/document'

export default function CatalogPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [search, setSearch] = useState('')

  const loadDocuments = async () => {
    const data = await getDocuments(search)
    setDocuments(data)

    const userId = getCurrentUserId()
    if (userId && search.trim() !== '') {
      try {
        await api.post('/search-history/', {
          user_id: userId,
          query: search,
        })
      } catch (err) {
        console.error('Ошибка фиксации поискового запроса:', err)
      }
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  return (
    <div className="content-stack">
      <h1 className="page-title">Каталог</h1>
      <SearchBar value={search} onChange={setSearch} onSearch={loadDocuments} />

      <section className="content-section">
        <div className="section-head">
          <h2>Документы</h2>
          <p>{search.trim() ? `Результаты по запросу: ${search}` : 'Весь каталог библиотеки'}</p>
        </div>

        <div className="grid">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} document={doc} trackView />
          ))}
        </div>
      </section>
    </div>
  )
}
