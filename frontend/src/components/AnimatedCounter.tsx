import { useEffect, useRef, useState } from 'react'
import { useInView } from 'framer-motion'

interface AnimatedCounterProps {
  value: number
  duration?: number
  suffix?: string
  prefix?: string
  className?: string
}

export default function AnimatedCounter({ value, duration = 1.4, suffix = '', prefix = '', className = '' }: AnimatedCounterProps) {
  const [display, setDisplay] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-40px' })
  const startTime = useRef<number | null>(null)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    if (!isInView) return
    startTime.current = null

    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp
      const elapsed = (timestamp - startTime.current) / 1000
      const progress = Math.min(elapsed / duration, 1)
      // easeOutExpo
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
      setDisplay(Math.round(eased * value))
      if (progress < 1) rafRef.current = requestAnimationFrame(animate)
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [isInView, value, duration])

  return (
    <span ref={ref} className={className}>
      {prefix}{display.toLocaleString('ru-RU')}{suffix}
    </span>
  )
}
