'use client'

import { useRef, useState, useEffect } from 'react'
import { useInView } from 'framer-motion'

export function CountUp({ target, suffix = '' }: { target: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const isVisible = useInView(ref, { once: true })
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!isVisible) return
    let frame = 0
    const totalFrames = 40
    const interval = setInterval(() => {
      frame++
      setCount(Math.round((frame / totalFrames) * target))
      if (frame >= totalFrames) {
        clearInterval(interval)
        setCount(target)
      }
    }, 30)
    return () => clearInterval(interval)
  }, [isVisible, target])

  return <span ref={ref}>{count}{suffix}</span>
}
