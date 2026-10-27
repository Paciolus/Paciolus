'use client'

/**
 * Motion elements for server components — Sprint 820.
 *
 * A server component cannot use `motion.*` from 'framer-motion' directly.
 * `framer-motion/client` solves that but defines ~170 element components in
 * one module, which landed in a shared chunk and added ~2.4 KB to every
 * route. This module re-exports only the elements the server-rendered
 * marketing pages use. Import as a namespace so call sites read the same:
 *
 *   import * as motion from '@/components/ui/motionClient'
 *   <motion.section initial={...} animate={...}>
 *
 * Props must be serializable (plain-object variants, no function variants).
 */

import { motion } from 'framer-motion'

export const div = motion.div
export const section = motion.section
export const span = motion.span
export const h2 = motion.h2
export const p = motion.p
export const ul = motion.ul
export const li = motion.li
