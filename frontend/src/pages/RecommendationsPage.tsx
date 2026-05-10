import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
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
      <motion.h1
        className="page-title"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
      >
        Рекомендации
      </motion.h1>

      <motion.section
        className="content-section"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="section-head">
          <h2>Персональная подборка</h2>
          <p>Сформировано по вашим просмотрам, избранному и оценкам</p>
        </div>
        <div className="grid">
          {documents.map((doc, i) => (
            <DocumentCard key={doc.id} document={doc} index={i} />
          ))}
        </div>
      </motion.section>
    </div>
  )
}
