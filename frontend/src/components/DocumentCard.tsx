import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import type { Document } from '../types/document'

interface DocumentCardProps {
  document: Document
  trackView?: boolean
  index?: number
}

export default function DocumentCard({ document, index = 0 }: DocumentCardProps) {
  const navigate = useNavigate()

  return (
    <motion.div
      className="document-card"
      onClick={() => navigate(`/documents/${document.id}`)}
      style={{ cursor: 'pointer' }}
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.38, delay: index * 0.07, ease: [0.4, 0, 0.2, 1] }}
      whileHover={{ y: -5, boxShadow: '0 16px 40px rgba(0,62,116,.14)', transition: { duration: 0.2 } }}
      whileTap={{ scale: 0.98 }}
    >
      <h3>{document.title}</h3>
      <p><strong>Автор:</strong> {document.authors || 'не указан'}</p>
      <p><strong>Год:</strong> {document.year || 'не указан'}</p>
      <p><strong>Категория:</strong> {document.category || 'не указана'}</p>
    </motion.div>
  )
}
