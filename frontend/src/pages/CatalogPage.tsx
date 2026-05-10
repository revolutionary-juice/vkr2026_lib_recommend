import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
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
        await api.post('/search-history/', { user_id: userId, query: search })
      } catch (err) {
        console.error('Ошибка фиксации поискового запроса:', err)
      }
    }
  }

  useEffect(() => { loadDocuments() }, [])

  return (
    <div className="content-stack">
      <motion.h1
        className="page-title"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
      >
        Каталог
      </motion.h1>

      <SearchBar value={search} onChange={setSearch} onSearch={loadDocuments} />

      <motion.section
        className="content-section"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="section-head">
          <h2>Документы</h2>
          <p>{search.trim() ? `Результаты по запросу: ${search}` : 'Весь каталог библиотеки'}</p>
        </div>
        <div className="grid">
          {documents.map((doc, i) => (
            <DocumentCard key={doc.id} document={doc} trackView index={i} />
          ))}
        </div>
      </motion.section>
    </div>
  )
}
