'use client'

import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import type { BenfordResult } from '@/types/jeTesting'

const BENFORD_EXPECTED: Record<number, number> = {
  1: 0.30103, 2: 0.17609, 3: 0.12494, 4: 0.09691,
  5: 0.07918, 6: 0.06695, 7: 0.05799, 8: 0.05115, 9: 0.04576,
}

function conformityColor(level: string): { bg: string; border: string; text: string; label: string } {
  switch (level) {
    case 'conforming':
      return { bg: 'bg-sage-500/10', border: 'border-sage-500/30', text: 'text-sage-400', label: 'Conforming' }
    case 'acceptable':
      return { bg: 'bg-sage-500/10', border: 'border-sage-500/20', text: 'text-sage-500', label: 'Acceptable' }
    case 'marginally_acceptable':
      return { bg: 'bg-oatmeal-500/10', border: 'border-oatmeal-500/30', text: 'text-oatmeal-400', label: 'Marginally Acceptable' }
    case 'nonconforming':
      return { bg: 'bg-clay-500/15', border: 'border-clay-500/40', text: 'text-clay-400', label: 'Non-Conforming' }
    default:
      return { bg: 'bg-obsidian-700', border: 'border-obsidian-600', text: 'text-oatmeal-500', label: level || 'N/A' }
  }
}

interface BenfordChartProps {
  benford: BenfordResult
}

export function BenfordChart({ benford }: BenfordChartProps) {
  if (!benford.passed_prechecks) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-5"
      >
        <h3 className="font-serif text-sm text-oatmeal-300 mb-3">
          Benford&apos;s Law Analysis
        </h3>
        <div className="flex items-center gap-3 p-4 bg-obsidian-900/40 rounded-lg">
          <div className="w-8 h-8 rounded-full bg-oatmeal-500/10 flex items-center justify-center flex-shrink-0">
            <span className="text-oatmeal-500 text-sm">i</span>
          </div>
          <div>
            <p className="font-sans text-sm text-oatmeal-400">Pre-check not passed</p>
            <p className="font-sans text-xs text-oatmeal-600 mt-0.5">
              {benford.precheck_message}
            </p>
          </div>
        </div>
        <p className="font-sans text-xs text-oatmeal-600 mt-3">
          {benford.total_count.toLocaleString()} entries examined, {benford.eligible_count.toLocaleString()} eligible
        </p>
      </motion.div>
    )
  }

  const conf = conformityColor(benford.conformity_level)

  // Build chart data
  const chartData = Array.from({ length: 9 }, (_, i) => {
    const digit = i + 1
    const key = String(digit)
    const actual = benford.actual_distribution[key] ?? 0
    const expected = BENFORD_EXPECTED[digit]
    const deviation = Math.abs(actual - expected)
    const isDeviated = benford.most_deviated_digits.includes(digit)
    return { digit: key, actual, expected, deviation, isDeviated }
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-serif text-sm text-oatmeal-300">
          Benford&apos;s Law Analysis
        </h3>
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${conf.bg} border ${conf.border}`}>
          <div className={`w-1.5 h-1.5 rounded-full ${benford.conformity_level === 'conforming' || benford.conformity_level === 'acceptable' ? 'bg-sage-400' : benford.conformity_level === 'marginally_acceptable' ? 'bg-oatmeal-400' : 'bg-clay-400'}`} />
          <span className={`text-xs font-sans font-medium ${conf.text}`}>{conf.label}</span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
            <XAxis
              dataKey="digit"
              tick={{ fill: '#9e9e9e', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={{ stroke: '#444' }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              tick={{ fill: '#757575', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#212121',
                border: '1px solid #444',
                borderRadius: '8px',
                fontSize: '12px',
                fontFamily: 'JetBrains Mono, monospace',
              }}
              labelStyle={{ color: '#EBE9E4' }}
              formatter={(value, name) => [
                `${(Number(value ?? 0) * 100).toFixed(2)}%`,
                name === 'actual' ? 'Actual' : 'Expected',
              ]}
            />
            <Bar dataKey="actual" radius={[4, 4, 0, 0]} maxBarSize={32}>
              {chartData.map((entry) => (
                <Cell
                  key={entry.digit}
                  fill={entry.isDeviated ? '#BC4749' : '#4A7C59'}
                  fillOpacity={entry.isDeviated ? 0.7 : 0.5}
                />
              ))}
            </Bar>
            {/* Expected distribution line using reference lines */}
            {chartData.map((entry) => (
              <ReferenceLine
                key={`ref-${entry.digit}`}
                y={entry.expected}
                stroke="transparent"
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend + Stats */}
      <div className="flex items-center gap-4 mt-3 text-xs font-sans">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-sage-500/50" />
          <span className="text-oatmeal-500">Conforming</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-clay-500/70" />
          <span className="text-oatmeal-500">Deviated</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-oatmeal-600">MAD: <span className="font-mono text-oatmeal-400">{benford.mad.toFixed(4)}</span></span>
          <span className="text-oatmeal-600">&chi;&sup2;: <span className="font-mono text-oatmeal-400">{benford.chi_squared.toFixed(2)}</span></span>
        </div>
      </div>

      <p className="font-sans text-xs text-oatmeal-600 mt-2">
        {benford.eligible_count.toLocaleString()} eligible entries analyzed out of {benford.total_count.toLocaleString()} total
      </p>
    </motion.div>
  )
}
