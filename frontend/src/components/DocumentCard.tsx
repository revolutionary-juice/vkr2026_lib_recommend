import { useNavigate } from 'react-router-dom'
import type { Document } from '../types/document'

interface DocumentCardProps {
  document: Document
  trackView?: boolean
}

export default function DocumentCard({ document }: DocumentCardProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/documents/${document.id}`)
  }

  return (
    <div className="document-card" onClick={handleClick} style={{ cursor: 'pointer' }}>
      <h3>{document.title}</h3>
      <p><strong>Автор:</strong> {document.authors || 'не указан'}</p>
      <p><strong>Год:</strong> {document.year || 'не указан'}</p>
      <p><strong>Категория:</strong> {document.category || 'не указана'}</p>
    </div>
  )
}
