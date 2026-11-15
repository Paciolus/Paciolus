import type { ReactNode } from 'react'
import Link from 'next/link'
import { POLICY_ROUTES } from '@/content/policies.generated'

/**
 * PolicyMarkdown — Sprint 862.
 *
 * Renders the published compliance documents (`docs/04-compliance/`, copied by
 * `scripts/sync_policy_docs.py`) as a server component. Deliberately small: it
 * handles the markdown those documents use — headings, paragraphs, bullet and
 * numbered lists, tables, bold, italics, inline code and links — and nothing
 * else, so there is no third-party parser in the bundle.
 *
 * Links: another published document goes to its site page; an external URL opens
 * normally; a link to a document the site does not publish (the archive, the
 * incident response plan …) renders as plain text, never a dead link.
 */

type Block =
  | { kind: 'heading'; level: number; text: string }
  | { kind: 'paragraph'; text: string }
  | { kind: 'list'; ordered: boolean; items: string[] }
  | { kind: 'table'; header: string[]; rows: string[][] }

const TABLE_ROW = /^\s*\|/
const BULLET = /^- (.*)$/
const NUMBERED = /^\d+\. (.*)$/
const HEADING = /^(#{1,4}) (.*)$/

function splitRow(line: string): string[] {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim())
}

export function parseBlocks(markdown: string): Block[] {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n')
  const blocks: Block[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i] ?? ''
    if (!line.trim()) { i++; continue }

    const heading = HEADING.exec(line)
    if (heading) {
      blocks.push({ kind: 'heading', level: heading[1]!.length, text: heading[2]!.trim() })
      i++
      continue
    }

    if (TABLE_ROW.test(line)) {
      const tableLines: string[] = []
      while (i < lines.length && TABLE_ROW.test(lines[i] ?? '')) tableLines.push(lines[i++] ?? '')
      const [head, , ...body] = tableLines
      blocks.push({ kind: 'table', header: splitRow(head ?? ''), rows: body.map(splitRow) })
      continue
    }

    const bullet = BULLET.exec(line)
    const numbered = NUMBERED.exec(line)
    if (bullet || numbered) {
      const ordered = Boolean(numbered)
      const pattern = ordered ? NUMBERED : BULLET
      const items: string[] = []
      while (i < lines.length) {
        const current = lines[i] ?? ''
        const match = pattern.exec(current)
        if (match) {
          items.push(match[1]!.trim())
        } else if (current.startsWith('  ') && current.trim() && items.length) {
          items[items.length - 1] += ' ' + current.trim() // continuation line
        } else {
          break
        }
        i++
      }
      blocks.push({ kind: 'list', ordered, items })
      continue
    }

    const para: string[] = []
    while (i < lines.length) {
      const current = lines[i] ?? ''
      if (!current.trim() || HEADING.test(current) || TABLE_ROW.test(current) || BULLET.test(current) || NUMBERED.test(current)) break
      para.push(current.trim())
      i++
    }
    blocks.push({ kind: 'paragraph', text: para.join(' ') })
  }
  return blocks
}

const INLINE = /(`[^`]+`)|(\*\*.+?\*\*)|(\*[^*\s][^*]*?\*)|(\[[^\]]+\]\([^)\s]+\))/

function resolveHref(href: string): { kind: 'internal' | 'external'; href: string } | null {
  if (/^https?:\/\//.test(href)) return { kind: 'external', href }
  if (href.startsWith('mailto:')) return { kind: 'external', href }
  const file = href.split('#')[0] ?? ''
  const route = POLICY_ROUTES[file]
  return route ? { kind: 'internal', href: route } : null
}

export function renderInline(text: string, keyPrefix = 'i'): ReactNode[] {
  const out: ReactNode[] = []
  let rest = text
  let n = 0
  while (rest) {
    const match = INLINE.exec(rest)
    if (!match) { out.push(rest); break }
    if (match.index > 0) out.push(rest.slice(0, match.index))
    const token = match[0]
    const key = `${keyPrefix}-${n++}`
    if (match[1]) {
      out.push(<code key={key} className="font-mono text-[0.9em] text-oatmeal-200 bg-obsidian-700/60 px-1 rounded-sm">{token.slice(1, -1)}</code>)
    } else if (match[2]) {
      out.push(<strong key={key} className="font-semibold text-oatmeal-100">{renderInline(token.slice(2, -2), key)}</strong>)
    } else if (match[3]) {
      out.push(<em key={key}>{renderInline(token.slice(1, -1), key)}</em>)
    } else {
      const link = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(token)
      const label = renderInline(link?.[1] ?? '', key)
      const target = resolveHref(link?.[2] ?? '')
      if (!target) {
        out.push(<span key={key}>{label}</span>)
      } else if (target.kind === 'internal') {
        out.push(<Link key={key} href={target.href} className="text-sage-400 hover:text-sage-300 underline">{label}</Link>)
      } else {
        out.push(<a key={key} href={target.href} className="text-sage-400 hover:text-sage-300 underline">{label}</a>)
      }
    }
    rest = rest.slice(match.index + token.length)
  }
  return out
}

export function PolicyMarkdown({ markdown }: { markdown: string }) {
  const blocks = parseBlocks(markdown)
  return (
    <div className="space-y-5 font-sans text-oatmeal-300 leading-relaxed">
      {blocks.map((block, b) => {
        const key = `b${b}`
        switch (block.kind) {
          case 'heading': {
            if (block.level === 1) return <h1 key={key} className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-2">{renderInline(block.text, key)}</h1>
            if (block.level === 2) return <h2 key={key} className="font-serif text-2xl text-oatmeal-100 pt-6 border-t border-obsidian-600">{renderInline(block.text, key)}</h2>
            if (block.level === 3) return <h3 key={key} className="font-serif text-xl text-oatmeal-100 pt-2">{renderInline(block.text, key)}</h3>
            return <h4 key={key} className="font-serif text-lg text-oatmeal-200">{renderInline(block.text, key)}</h4>
          }
          case 'paragraph':
            return <p key={key}>{renderInline(block.text, key)}</p>
          case 'list': {
            const items = block.items.map((item, k) => <li key={`${key}-${k}`}>{renderInline(item, `${key}-${k}`)}</li>)
            return block.ordered
              ? <ol key={key} className="list-decimal pl-6 space-y-2">{items}</ol>
              : <ul key={key} className="list-disc pl-6 space-y-2">{items}</ul>
          }
          case 'table':
            return (
              <div key={key} className="overflow-x-auto">
                <table className="w-full border-collapse text-sm tabular-nums">
                  <thead>
                    <tr className="border-b border-obsidian-500">
                      {block.header.map((cell, c) => (
                        <th key={c} className="text-left font-serif font-normal text-oatmeal-100 py-2 pr-4 align-bottom">{renderInline(cell, `${key}-h${c}`)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {block.rows.map((row, r) => (
                      <tr key={r} className="border-b border-obsidian-700">
                        {row.map((cell, c) => (
                          <td key={c} className="py-2 pr-4 align-top text-oatmeal-300">{renderInline(cell, `${key}-${r}-${c}`)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
        }
      })}
    </div>
  )
}
