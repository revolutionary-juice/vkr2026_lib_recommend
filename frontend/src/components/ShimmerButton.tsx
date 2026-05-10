import { motion } from 'framer-motion'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ShimmerButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'ghost'
}

export default function ShimmerButton({ children, variant = 'primary', style, ...props }: ShimmerButtonProps) {
  const isPrimary = variant === 'primary'

  return (
    <motion.button
      {...(props as any)}
      style={{
        position: 'relative', overflow: 'hidden',
        background: isPrimary ? 'var(--dvfu-dark)' : 'transparent',
        border: isPrimary ? 'none' : '1.5px solid var(--dvfu-dark)',
        color: isPrimary ? '#fff' : 'var(--dvfu-dark)',
        borderRadius: 8, padding: '10px 20px',
        fontWeight: 600, fontSize: 14,
        cursor: 'pointer', display: 'inline-flex',
        alignItems: 'center', gap: 8,
        ...style,
      }}
      whileHover={{ scale: 1.02, transition: { duration: 0.15 } }}
      whileTap={{ scale: 0.97 }}
    >
      {/* shimmer sweep */}
      <motion.span
        style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none',
          background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.25) 50%, transparent 60%)',
          backgroundSize: '200% 100%',
        }}
        initial={{ backgroundPositionX: '200%' }}
        whileHover={{ backgroundPositionX: '-50%', transition: { duration: 0.5, ease: 'easeInOut' } }}
      />
      {children}
    </motion.button>
  )
}
