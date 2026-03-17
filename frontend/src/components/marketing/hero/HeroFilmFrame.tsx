// Individual frame components for upload, analyze, and export animation layers.
'use client'

import { motion } from 'framer-motion'
import { BrandIcon } from '@/components/shared'
import { ANALYSIS_LABEL_SHORT } from '@/utils/constants'
import { SPRING } from '@/utils/themeUtils'
import { usePhaseTimer, useCountAnimation } from './useHeroAnimation'
import type { MotionValue } from 'framer-motion'

// ── Cursor SVG ──────────────────────────────────────────────────────

function CursorIcon({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true">
      <path d="M5 2L19 12L12 13L15 21L12 22L9 14L5 17V2Z" />
    </svg>
  )
}

// ── Tool Tiles Data ──────────────────────────────────────────────────

const TOOL_TILES = [
  { name: 'Journal Entry Testing', activates: true },
  { name: 'AP Testing', activates: true },
  { name: 'Payroll Testing', activates: true },
  { name: 'Revenue Testing', activates: true },
  { name: 'AR Aging', activates: true },
  { name: 'Fixed Assets Testing', activates: false },
  { name: 'Inventory Testing', activates: false },
  { name: 'Bank Reconciliation', activates: true },
  { name: 'Three-Way Match', activates: false },
  { name: 'Multi-Period TB', activates: true },
  { name: 'Statistical Sampling', activates: true },
  { name: 'Multi-Currency', activates: true },
] as const

const FORMAT_BADGES = ['CSV', 'XLSX', 'OFX', 'PDF', 'QBO'] as const

// ── Upload Layer — Cursor + File Card ───────────────────────────────

const UPLOAD_PHASES = [300, 1000, 1500, 2800, 3600, 4400] as const
const DATA_LINES = ['847 transactions', '62 accounts', 'FY 2025'] as const

export function UploadLayer({ opacity, isActive }: { opacity: MotionValue<number>; isActive: boolean }) {
  const phase = usePhaseTimer(isActive, UPLOAD_PHASES)

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6"
      style={{ opacity }}
    >
      {/* Stage — file card source + drop zone + cursor */}
      <div className="relative w-full max-w-[300px]">
        {/* Source file card at rest (upper-right, before cursor grabs it) */}
        {phase < 3 && (
          <motion.div
            className="absolute -top-6 -right-2 z-10"
            initial={{ opacity: 0, y: 8 }}
            animate={
              phase >= 2
                ? { opacity: 1, y: -4, scale: 1.05 }
                : { opacity: 1, y: 0, scale: 1 }
            }
            transition={
              phase >= 2
                ? { duration: 0.2, ease: 'easeOut' as const }
                : { duration: 0.4, ease: 'easeOut' as const }
            }
          >
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-white border shadow-sm whitespace-nowrap transition-shadow duration-200 ${
              phase >= 2 ? 'border-sage-400/40 shadow-md' : 'border-obsidian-200'
            }`}>
              <BrandIcon name="file-plus" className="w-4 h-4 text-sage-500 flex-shrink-0" />
              <span className="font-mono text-[10px] text-obsidian-700">FY2025.xlsx</span>
            </div>
          </motion.div>
        )}

        {/* Drop zone target (always visible) */}
        <motion.div
          className="relative flex flex-col items-center justify-center gap-2 py-8 px-6 rounded-xl border-2 border-dashed overflow-hidden"
          animate={
            phase >= 3 && phase < 4
              ? {
                  borderColor: [
                    'rgba(74,124,89,0.2)',
                    'rgba(74,124,89,0.6)',
                    'rgba(74,124,89,0.2)',
                  ],
                }
              : phase >= 4
                ? { borderColor: 'rgba(74,124,89,0.4)' }
                : { borderColor: 'rgba(74,124,89,0.15)' }
          }
          transition={
            phase >= 3 && phase < 4
              ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' as const }
              : { duration: 0.3 }
          }
        >
          {/* Sage glow pulse on drop */}
          {phase >= 4 && (
            <motion.div
              className="absolute inset-0 bg-sage-400/10 rounded-xl pointer-events-none"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            />
          )}

          {/* Placeholder text (before file drops in) */}
          {phase < 4 && (
            <motion.div
              className="flex flex-col items-center gap-1"
              animate={phase >= 3 ? { opacity: 0.3 } : { opacity: 0.6 }}
            >
              <BrandIcon name="cloud-upload" className="w-8 h-8 text-obsidian-300" />
              <span className="font-sans text-xs text-obsidian-400">Drop your file here</span>
            </motion.div>
          )}

          {/* Settled file card (after drop) */}
          {phase >= 4 && (
            <motion.div
              className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-sage-400/40 shadow-sm w-full"
              initial={{ scale: 1.1, opacity: 0, y: -8 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              transition={SPRING.bouncy}
            >
              <BrandIcon name="file-plus" className="w-6 h-6 text-sage-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-mono text-xs text-obsidian-800 font-medium truncate">
                  Your_Company_FY2025.xlsx
                </p>
                <p className="font-mono text-[10px] text-obsidian-400">2.4 MB</p>
              </div>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, ...SPRING.bouncy }}
              >
                <BrandIcon name="checkmark" className="w-4 h-4 text-sage-500" />
              </motion.div>
            </motion.div>
          )}
        </motion.div>

        {/* Cursor — persists across phases 1→3, position driven by phase */}
        {phase >= 1 && phase < 4 && (
          <motion.div
            className="absolute pointer-events-none z-20"
            initial={{ x: 260, y: -50, opacity: 0 }}
            animate={
              phase >= 3
                ? { x: 90, y: 55, opacity: 1 }
                : phase >= 2
                  ? { x: 195, y: -15, opacity: 1 }
                  : { x: 220, y: -30, opacity: 1 }
            }
            transition={
              phase >= 3
                ? { duration: 1.1, ease: [0.32, 0.0, 0.22, 1] }
                : { duration: 0.6, ease: [0.32, 0.0, 0.22, 1] }
            }
          >
            <CursorIcon className="w-5 h-5 text-obsidian-600 drop-shadow-md" />
            {/* File card attaches to cursor during drag */}
            {phase >= 3 && (
              <motion.div
                className="absolute top-3 left-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-obsidian-200 shadow-lg whitespace-nowrap"
                initial={{ rotate: -6 }}
                animate={{ rotate: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut' as const }}
              >
                <BrandIcon name="file-plus" className="w-4 h-4 text-sage-500 flex-shrink-0" />
                <span className="font-mono text-[10px] text-obsidian-700">FY2025.xlsx</span>
              </motion.div>
            )}
          </motion.div>
        )}
      </div>

      {/* Recognition — three data lines resolve sequentially */}
      <div className="flex flex-col items-center gap-1">
        {DATA_LINES.map((line, i) => (
          <motion.p
            key={line}
            className="font-mono text-sm font-medium text-obsidian-700"
            animate={phase >= 5 ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
            transition={{ delay: i * 0.15, duration: 0.25, ease: 'easeOut' as const }}
          >
            {line}
          </motion.p>
        ))}
      </div>

      {/* Format badges */}
      <motion.div
        className="flex items-center gap-2"
        animate={phase >= 6 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        {FORMAT_BADGES.map((fmt, i) => (
          <span key={fmt}>
            <span className="font-mono text-[10px] text-sage-600/70 font-medium">
              {fmt}
            </span>
            {i < FORMAT_BADGES.length - 1 && (
              <span className="text-obsidian-300 ml-2">&middot;</span>
            )}
          </span>
        ))}
      </motion.div>

      {/* Speed indicator */}
      <motion.p
        className="font-mono text-[11px] text-sage-600 uppercase tracking-widest"
        animate={phase >= 6 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 0.15, duration: 0.3 }}
      >
        {ANALYSIS_LABEL_SHORT}
      </motion.p>
    </motion.div>
  )
}

// ── Analyze Layer — Scanning Matrix ─────────────────────────────────

const ANALYZE_PHASES = [0, 800, 2400, 5500, 7500] as const

export function AnalyzeLayer({ opacity, isActive }: { opacity: MotionValue<number>; isActive: boolean }) {
  const phase = usePhaseTimer(isActive, ANALYZE_PHASES)
  const testCount = useCountAnimation(108, 2.0, phase >= 3)

  // Pre-compute which tiles activate and their stagger indices
  const activatingTiles: number[] = []
  TOOL_TILES.forEach((tile, i) => {
    if (tile.activates) activatingTiles.push(i)
  })

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4"
      style={{ opacity }}
    >
      {/* 4x3 tool grid with scan effect */}
      <div className="relative w-full max-w-[280px]">
        {/* Scanning line */}
        {phase >= 1 && phase < 4 && (
          <motion.div
            className="absolute top-0 bottom-0 w-0.5 bg-gradient-to-b from-transparent via-sage-400/60 to-transparent z-10 pointer-events-none"
            initial={{ left: 0 }}
            animate={{ left: '100%' }}
            transition={{ duration: 2.0, repeat: Infinity, ease: 'linear' as const }}
          />
        )}

        <div className="grid grid-cols-3 gap-1.5">
          {TOOL_TILES.map((tile, i) => {
            const activationIdx = activatingTiles.indexOf(i)
            const isActiveTile = tile.activates && phase >= 2
            const tileDelay = activationIdx >= 0 ? activationIdx * 0.15 : 0
            // Each tile needs ~0.15s stagger, 9 tiles = ~1.35s total
            const isComplete = tile.activates && phase >= 3

            if (tile.activates) {
              return (
                <motion.div
                  key={tile.name}
                  className="relative rounded-lg border bg-white px-1.5 py-2 flex flex-col items-center justify-center gap-1 overflow-hidden"
                  animate={
                    isComplete
                      ? { borderColor: 'rgba(74,124,89,0.5)', opacity: 1 }
                      : isActiveTile
                        ? { borderColor: 'rgba(74,124,89,0.3)', opacity: 1 }
                        : { borderColor: 'rgba(176,176,176,0.3)', opacity: 0.5 }
                  }
                  transition={{ delay: tileDelay, duration: 0.2 }}
                >
                  <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-obsidian-700">
                    {tile.name}
                  </span>

                  {/* Mini progress bar → checkmark */}
                  <div className="w-full h-1 relative">
                    {isActiveTile && !isComplete && (
                      <motion.div
                        className="absolute inset-y-0 left-0 rounded-full bg-sage-400/60"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{ delay: tileDelay, duration: 0.6, ease: 'easeOut' as const }}
                      />
                    )}
                    {isComplete && (
                      <motion.div
                        className="absolute inset-0 flex items-center justify-center"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: tileDelay + 0.1, ...SPRING.bouncy }}
                      >
                        <BrandIcon name="checkmark" className="w-3 h-3 text-sage-500" />
                      </motion.div>
                    )}
                  </div>

                  {/* Sage flash overlay on activation */}
                  {isActiveTile && (
                    <motion.div
                      className="absolute inset-0 bg-sage-400 pointer-events-none rounded-lg"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: [0, 0.12, 0] }}
                      transition={{ delay: tileDelay, duration: 0.3, ease: 'easeOut' as const }}
                    />
                  )}
                </motion.div>
              )
            }

            return (
              <div
                key={tile.name}
                className="rounded-lg border border-obsidian-200/30 bg-oatmeal-100/50 px-1.5 py-2 flex items-center justify-center opacity-30"
              >
                <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-obsidian-400 line-through decoration-obsidian-200">
                  {tile.name}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Test counter */}
      <div className="flex items-center gap-2">
        <motion.p
          className="font-mono text-sm text-obsidian-700 font-medium tabular-nums"
          animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {testCount}/108 tests
        </motion.p>

        {/* Findings badge */}
        <motion.span
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-clay-50 border border-clay-200/50"
          animate={phase >= 4 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
          transition={SPRING.snappy}
        >
          <BrandIcon name="warning-triangle" className="w-3 h-3 text-clay-500" />
          <span className="font-sans text-[10px] font-medium text-clay-600">3 findings</span>
        </motion.span>
      </div>

      {/* Summary line */}
      <motion.p
        className="font-sans text-xs text-obsidian-500 text-center"
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        108 tests run across 9 tools &middot; 3 findings flagged
      </motion.p>
    </motion.div>
  )
}

// ── Export Layer — Progress Bar Download ─────────────────────────────

const EXPORT_PHASES = [0, 200, 500, 900, 2200, 2800] as const

export function ExportLayer({ opacity, isActive }: { opacity: MotionValue<number>; isActive: boolean }) {
  const phase = usePhaseTimer(isActive, EXPORT_PHASES)
  const fileSize = useCountAnimation(2400, 1.2, phase >= 4)

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-5"
      style={{ opacity }}
    >
      <div className="w-full max-w-[320px] flex flex-col gap-2.5">
        {/* Workpapers row — slides in from right */}
        <motion.div
          className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-obsidian-200/40 shadow-sm"
          animate={
            phase >= 1
              ? { x: 0, opacity: 1 }
              : { x: 50, opacity: 0 }
          }
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <BrandIcon name="spreadsheet" className="w-5 h-5 text-sage-500 flex-shrink-0" />
          <span className="font-sans text-sm text-obsidian-800 font-medium flex-1 min-w-0 truncate">
            Your_Company_Workpapers.xlsx
          </span>
          <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-500 flex-shrink-0" />
        </motion.div>

        {/* PDF memos row — slides in from right (staggered) */}
        <motion.div
          className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-obsidian-200/40 shadow-sm"
          animate={
            phase >= 2
              ? { x: 0, opacity: 1 }
              : { x: 50, opacity: 0 }
          }
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <BrandIcon name="document-blank" className="w-5 h-5 text-obsidian-500 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="font-sans text-sm text-obsidian-800 font-medium">
              17 PDF Memos
            </span>
            <p className="font-sans text-[11px] text-obsidian-400 truncate mt-0.5">
              JE Testing &middot; Revenue &middot; AP &middot; Sampling &middot; ...
            </p>
          </div>
          <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-500 flex-shrink-0" />
        </motion.div>
      </div>

      {/* Download button with progress bar */}
      <div className="w-full max-w-[320px]">
        <motion.div
          className="relative w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg overflow-hidden"
          animate={
            phase >= 3
              ? { opacity: 1 }
              : { opacity: 0.5 }
          }
          transition={{ duration: 0.2 }}
        >
          {/* Background track */}
          <div className="absolute inset-0 bg-sage-100 rounded-lg" />

          {/* Progress fill */}
          <motion.div
            className="absolute inset-y-0 left-0 bg-sage-500 rounded-lg"
            initial={{ width: '0%' }}
            animate={phase >= 3 ? { width: '100%' } : { width: '0%' }}
            transition={
              phase >= 3
                ? { duration: 1.2, ease: [0.25, 0.1, 0.25, 1] }
                : { duration: 0 }
            }
          />

          {/* Button content */}
          <div className="relative z-10 flex items-center gap-2">
            {phase >= 5 ? (
              <motion.div
                initial={{ scale: 0, rotate: -90 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={SPRING.bouncy}
              >
                <BrandIcon name="checkmark" className="w-4 h-4 text-white" />
              </motion.div>
            ) : (
              <BrandIcon name="download-arrow" className="w-4 h-4 text-obsidian-700" />
            )}
            <span className={`font-sans text-sm font-medium transition-colors duration-300 ${
              phase >= 4 ? 'text-white' : 'text-obsidian-700'
            }`}>
              {phase >= 5 ? 'Download Complete' : 'Download Engagement File'}
            </span>
          </div>
        </motion.div>
      </div>

      {/* File size counter + checkmark */}
      <div className="flex items-center gap-3">
        <motion.p
          className="font-mono text-xs text-obsidian-500 tabular-nums"
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {(fileSize / 1000).toFixed(1)} MB
        </motion.p>

        {phase >= 5 && (
          <motion.div
            className="flex items-center gap-1"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={SPRING.bouncy}
          >
            <div className="w-1.5 h-1.5 rounded-full bg-sage-400" />
            <span className="font-sans text-[10px] text-sage-600 font-medium">Ready</span>
          </motion.div>
        )}
      </div>

      {/* Zero-storage whisper */}
      <motion.p
        className="font-sans text-[11px] text-obsidian-400 italic text-center"
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
      >
        Processed in-memory and immediately destroyed. Raw financial data is never stored.
      </motion.p>
    </motion.div>
  )
}
