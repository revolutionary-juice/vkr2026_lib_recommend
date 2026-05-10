import { useEffect, useState } from 'react'
import { motion, type Variants } from 'framer-motion'
import { getPopularDocuments, getRecentDocuments } from '../api/documents'
import type { Document } from '../types/document'
import DocumentCard from '../components/DocumentCard'
import { DocumentCardSkeleton } from '../components/Skeleton'

const sectionVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.4, delay: i * 0.12, ease: 'easeOut' }
  })
}

export default function HomePage() {
  const [popular, setPopular] = useState<Document[]>([])
  const [recent, setRecent]   = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getPopularDocuments(), getRecentDocuments()]).then(([p, r]) => {
      setPopular(p); setRecent(r); setLoading(false)
    })
  }, [])

  return (
    <div className="content-stack">
      <motion.h1
        className="page-title"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
      >
        Главная
      </motion.h1>

      <motion.section className="content-section" custom={0} variants={sectionVariants} initial="hidden" animate="visible">
        <div className="section-head">
          <h2>Популярные документы</h2>
          <p>Подборка наиболее востребованных материалов</p>
        </div>
        <div className="grid">
          {loading
            ? Array.from({ length: 3 }).map((_, i) => <DocumentCardSkeleton key={i} />)
            : popular.map((doc, i) => <DocumentCard key={doc.id} document={doc} index={i} />)}
        </div>
      </motion.section>

      <motion.section className="content-section" custom={1} variants={sectionVariants} initial="hidden" animate="visible">
        <div className="section-head">
          <h2>Новые документы</h2>
          <p>Последние добавления в каталог</p>
        </div>
        <div className="grid">
          {loading
            ? Array.from({ length: 3 }).map((_, i) => <DocumentCardSkeleton key={i} />)
            : recent.map((doc, i) => <DocumentCard key={doc.id} document={doc} index={i} />)}
        </div>
      </motion.section>
    </div>
  )
}
