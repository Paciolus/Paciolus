/**
 * Sprint 887 (review OUT-30): result components use the approved vocabulary.
 *
 * Paciolus reports what its tests flagged; a test with nothing flagged is
 * "no exceptions flagged" — never clean, passed or verified — and software
 * output is "items flagged", not findings. The backend scans rendered memo text
 * and its label mappings (test_memo_banned_phrases.py); this scans the screens'
 * result components, label maps included, for the same words.
 */
import fs from 'fs'
import path from 'path'

const COMPONENTS = path.join(__dirname, '..', 'components')

// Folders that render tool results, flags and their labels.
const RESULT_DIRS = [
  'shared/testing',
  'jeTesting',
  'apTesting',
  'payrollTesting',
  'revenueTesting',
  'arAging',
  'fixedAssetTesting',
  'inventoryTesting',
  'bankRec',
  'threeWayMatch',
  'trialBalance',
  'multiPeriod',
  'statisticalSampling',
  'diagnostic',
  'diagnostics',
  'preflight',
  'leadSheet',
  'sod',
  'intercompany',
  'w2Reconciliation',
  'form1099',
  'bookToTax',
  'cashFlowProjector',
]

const BANNED: Array<[RegExp, string]> = [
  [/\bclean\b/i, "say 'no exceptions flagged'"],
  [/\b(?:not )?passed\b/i, 'say what was or was not met'],
  [/\bverified\b/i, 'say what was compared'],
  [/\bfindings?\b/i, "say 'items flagged'"],
]

function sourceFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) return sourceFiles(full)
    return /\.tsx?$/.test(entry.name) ? [full] : []
  })
}

/** Text a user can see: JSX text and string/template literals, with comments removed. */
function visibleText(source: string): string[] {
  const code = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '')
  const pieces: string[] = []
  for (const m of code.matchAll(/>([^<>{}]+)</g)) pieces.push(m[1])
  for (const m of code.matchAll(/'([^'\n]*)'|"([^"\n]*)"|`([^`]*)`/g)) pieces.push(m[1] ?? m[2] ?? m[3] ?? '')
  // A bare identifier ('findings', 'top_findings') is a data key, not text.
  return pieces.map(p => p.trim()).filter(p => p && !/^[a-z_]+$/.test(p))
}

describe('result vocabulary (Sprint 887 / OUT-30)', () => {
  const files = RESULT_DIRS.flatMap(d => sourceFiles(path.join(COMPONENTS, d)))

  it('finds the result components', () => {
    expect(files.length).toBeGreaterThan(50)
  })

  it('no result component shows clean, passed, verified or findings', () => {
    const hits: string[] = []
    for (const file of files) {
      for (const text of visibleText(fs.readFileSync(file, 'utf8'))) {
        for (const [rx, why] of BANNED) {
          if (rx.test(text)) hits.push(`${path.relative(COMPONENTS, file)}: "${text.slice(0, 80)}" — ${why}`)
        }
      }
    }
    expect(hits).toEqual([])
  })

  it('the scan catches the wording it bans', () => {
    const sample = `<p className="x">Clean</p><p>Pre-check not passed</p>`
    const caught = visibleText(sample).filter(t => BANNED.some(([rx]) => rx.test(t)))
    expect(caught).toEqual(['Clean', 'Pre-check not passed'])
  })
})
