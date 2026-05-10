import { motion } from 'framer-motion'

interface SkeletonProps {
  className?: string
  height?: number | string
  width?: number | string
  borderRadius?: number | string
}

export function Skeleton({ className = '', height = 20, width = '100%', borderRadius = 8 }: SkeletonProps) {
  return (
    <motion.div
      className={className}
      style={{ height, width, borderRadius, overflow: 'hidden', background: 'var(--gray-200, #E9EDF3)', position: 'relative' }}
    >
      <motion.div
        style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.7) 50%, transparent 100%)',
        }}
        animate={{ x: ['-100%', '100%'] }}
        transition={{ duration: 1.4, repeat: Infinity, ease: 'linear' }}
      />
    </motion.div>
  )
}

export function DocumentCardSkeleton() {
  return (
    <div className="document-card" style={{ gap: 14, cursor: 'default' }}>
      <Skeleton height={22} width="75%" borderRadius={6} />
      <Skeleton height={14} width="50%" borderRadius={4} />
      <Skeleton height={14} width="40%" borderRadius={4} />
      <Skeleton height={14} width="55%" borderRadius={4} />
    </div>
  )
}
