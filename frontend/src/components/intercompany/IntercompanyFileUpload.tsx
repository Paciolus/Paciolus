'use client'

/**
 * Intercompany long-format CSV upload surface — Sprint 689c.
 *
 * One file drop. Rows are parsed client-side and pivoted into a
 * grouped-entity JSON payload matching /audit/intercompany-elimination.
 */

import { useCallback, useMemo, useState } from 'react'
import {
  IntercompanyCsvParseError,
  buildRequest,
  parseIntercompanyCsv,
  readFileAsText,
} from '@/components/intercompany/parseCsv'
import { FileDropZone } from '@/components/shared'
import type {
  IntercompanyEliminationRequest,
  IntercompanyEntityTBRequest,
} from '@/types/intercompany'

interface IntercompanyFileUploadProps {
  onAnalyze: (payload: IntercompanyEliminationRequest) => void
  onExport: (payload: IntercompanyEliminationRequest) => void
  loading: boolean
}

interface ParsedState {
  entities: IntercompanyEntityTBRequest[]
  totalRows: number
  intercompanyRows: number
  warnings: string[]
}

export function IntercompanyFileUpload({ onAnalyze, onExport, loading }: IntercompanyFileUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [tolerance, setTolerance] = useState('1.00')
  const [parsed, setParsed] = useState<ParsedState | null>(null)
  const [parseError, setParseError] = useState('')

  const handleFile = useCallback(async (f: File) => {
    setFile(f)
    setParseError('')
    try {
      const text = await readFileAsText(f)
      const result = parseIntercompanyCsv(text)
      setParsed(result)
    } catch (err) {
      setParsed(null)
      setParseError(
        err instanceof IntercompanyCsvParseError
          ? err.message
          : 'Failed to parse CSV.',
      )
    }
  }, [])

  const payload = useMemo<IntercompanyEliminationRequest | null>(() => {
    if (!parsed || parsed.entities.length < 2) return null
    return buildRequest(parsed.entities, tolerance)
  }, [parsed, tolerance])

  const canRun = payload !== null && !loading

  return (
    <div className="theme-card p-6">
      <h2 className="font-serif text-lg text-content-primary mb-2">Upload Multi-Entity Trial Balance</h2>
      <p className="font-sans text-sm text-content-secondary mb-5">
        Export a single long-format CSV from your consolidation workbook or ERP group-reporting
        module. Rows are pivoted client-side into per-entity trial balances before analysis.
      </p>

      <FileDropZone
        label="Multi-entity TB (CSV)"
        hint="Drop intercompany_tb.csv or click to browse"
        file={file}
        onFileSelect={handleFile}
        disabled={loading}
        accept=".csv,.tsv,.txt"
      />

      <div className="mt-3 text-xs font-sans text-content-tertiary">
        <span>Columns: </span>
        <code className="font-mono">entity_id, entity_name, account, debit, credit, counterparty_entity</code>.
        Set <code className="font-mono">counterparty_entity</code> on rows that represent intercompany balances;
        leave blank on standalone accounts.
      </div>

      {parsed && (
        <div className="mt-3 p-3 rounded-lg border border-sage-200 bg-sage-50 text-sage-800 text-xs font-sans">
          <div>
            <span className="font-medium">{parsed.entities.length}</span> entities,{' '}
            <span className="font-medium">{parsed.totalRows.toLocaleString()}</span> total rows,{' '}
            <span className="font-medium">{parsed.intercompanyRows.toLocaleString()}</span> intercompany rows parsed.
          </div>
          {parsed.warnings.map(w => (
            <div key={w} className="mt-1 text-obsidian-700">⚠ {w}</div>
          ))}
        </div>
      )}

      {parseError && (
        <div className="mt-3 p-3 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
          {parseError}
        </div>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs font-sans text-content-secondary">
          <span>Tolerance</span>
          <input
            type="text"
            value={tolerance}
            onChange={e => setTolerance(e.target.value)}
            disabled={loading}
            className="w-24 px-2 py-1 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500"
            aria-label="Reconciliation tolerance"
          />
        </label>
        <button
          type="button"
          onClick={() => payload && onAnalyze(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg bg-sage-600 text-oatmeal-50 font-sans font-medium hover:bg-sage-700 disabled:bg-obsidian-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Consolidating…' : 'Run Consolidation'}
        </button>
        <button
          type="button"
          onClick={() => payload && onExport(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg border border-theme bg-surface-card text-content-primary font-sans font-medium hover:bg-oatmeal-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Download CSV
        </button>
      </div>
    </div>
  )
}
