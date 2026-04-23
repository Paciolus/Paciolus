'use client'

/**
 * SoD dual-CSV upload surface — Sprint 689b.
 *
 * Two file drops (users + roles), each parsed client-side before the
 * analyze button posts JSON to /audit/sod/analyze. Enterprise-tier gated
 * upstream; this component assumes the caller has already cleared the tier.
 */

import { useCallback, useMemo, useState } from 'react'
import { FileDropZone } from '@/components/shared'
import {
  CsvParseError,
  parseRolesCsv,
  parseUsersCsv,
  readFileAsText,
} from '@/components/sod/parseCsv'
import type { SODAnalysisRequest, SODRolePermission, SODUserAssignment } from '@/types/sod'

interface SODFileUploadProps {
  onAnalyze: (payload: SODAnalysisRequest) => void
  onExport: (payload: SODAnalysisRequest) => void
  loading: boolean
}

interface ParsedState {
  assignments: SODUserAssignment[]
  permissions: SODRolePermission[]
}

export function SODFileUpload({ onAnalyze, onExport, loading }: SODFileUploadProps) {
  const [usersFile, setUsersFile] = useState<File | null>(null)
  const [rolesFile, setRolesFile] = useState<File | null>(null)
  const [parsed, setParsed] = useState<ParsedState>({ assignments: [], permissions: [] })
  const [parseError, setParseError] = useState('')

  const handleUsersFile = useCallback(async (file: File) => {
    setUsersFile(file)
    setParseError('')
    try {
      const text = await readFileAsText(file)
      const { assignments } = parseUsersCsv(text)
      setParsed(prev => ({ ...prev, assignments }))
    } catch (err) {
      setParsed(prev => ({ ...prev, assignments: [] }))
      setParseError(err instanceof CsvParseError ? err.message : 'Failed to parse users CSV.')
    }
  }, [])

  const handleRolesFile = useCallback(async (file: File) => {
    setRolesFile(file)
    setParseError('')
    try {
      const text = await readFileAsText(file)
      const { permissions } = parseRolesCsv(text)
      setParsed(prev => ({ ...prev, permissions }))
    } catch (err) {
      setParsed(prev => ({ ...prev, permissions: [] }))
      setParseError(err instanceof CsvParseError ? err.message : 'Failed to parse roles CSV.')
    }
  }, [])

  const payload = useMemo<SODAnalysisRequest | null>(() => {
    if (parsed.assignments.length === 0 || parsed.permissions.length === 0) return null
    return {
      user_assignments: parsed.assignments,
      role_permissions: parsed.permissions,
    }
  }, [parsed])

  const canAnalyze = payload !== null && !loading

  return (
    <div className="theme-card p-6">
      <h2 className="font-serif text-lg text-content-primary mb-2">Upload Matrices</h2>
      <p className="font-sans text-sm text-content-secondary mb-5">
        Export your user-to-role and role-to-permission matrices from your IAM, ERP, or HRIS system as CSV,
        then drop both files below. Analysis runs against the hardcoded SoD rule library plus any custom rules.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <FileDropZone
            label="Users → Roles"
            hint="Drop users.csv or click to browse"
            file={usersFile}
            onFileSelect={handleUsersFile}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: <code className="font-mono">user_id, user_name, role_codes</code>. Role codes
            pipe-delimited (e.g. <code className="font-mono">AP_ADMIN|JE_POSTER</code>).
            {parsed.assignments.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.assignments.length} user{parsed.assignments.length === 1 ? '' : 's'} parsed.</span>
            )}
          </p>
        </div>
        <div>
          <FileDropZone
            label="Roles → Permissions"
            hint="Drop roles.csv or click to browse"
            file={rolesFile}
            onFileSelect={handleRolesFile}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: <code className="font-mono">role_code, permissions</code>. Permissions
            pipe-delimited.
            {parsed.permissions.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.permissions.length} role{parsed.permissions.length === 1 ? '' : 's'} parsed.</span>
            )}
          </p>
        </div>
      </div>

      {parseError && (
        <div className="mb-4 p-3 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
          {parseError}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => payload && onAnalyze(payload)}
          disabled={!canAnalyze}
          className="px-5 py-2.5 rounded-lg bg-sage-600 text-oatmeal-50 font-sans font-medium hover:bg-sage-700 disabled:bg-obsidian-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analyzing…' : 'Run SoD Analysis'}
        </button>
        <button
          type="button"
          onClick={() => payload && onExport(payload)}
          disabled={!canAnalyze}
          className="px-5 py-2.5 rounded-lg border border-theme bg-surface-card text-content-primary font-sans font-medium hover:bg-oatmeal-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Download CSV
        </button>
      </div>
    </div>
  )
}
