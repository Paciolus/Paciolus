import * as motion from 'framer-motion/client'

/** Section wrapper with consistent heading pattern */
export function ModuleSection({
  id,
  meta,
  title,
  subtitle,
  surface = '',
  children,
}: {
  id: string
  meta: string
  title: string
  subtitle?: string
  surface?: string
  children: React.ReactNode
}) {
  return (
    <section id={id} className={`py-24 px-6 ${surface}`} aria-labelledby={`${id}-heading`}>
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-block type-meta text-sage-400 mb-3"
          >
            {meta}
          </motion.span>
          <motion.h2
            id={`${id}-heading`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="type-headline text-oatmeal-100 mb-4"
          >
            {title}
          </motion.h2>
          {subtitle && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="font-sans text-oatmeal-400"
            >
              {subtitle}
            </motion.p>
          )}
        </div>
        {children}
      </div>
    </section>
  )
}
