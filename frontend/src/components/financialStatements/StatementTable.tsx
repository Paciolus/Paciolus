import { formatCurrency } from '@/utils'
import type { StatementLineItem } from './types'

export function StatementTable({ items }: { items: StatementLineItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-obsidian-600">
            <th className="text-left py-2 px-3 text-oatmeal-500 text-xs uppercase tracking-wider font-sans font-medium">
              Description
            </th>
            <th className="text-right py-2 px-3 text-oatmeal-500 text-xs uppercase tracking-wider font-sans font-medium w-40">
              Amount
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => {
            const isSectionHeader = item.indentLevel === 0 && !item.isSubtotal && !item.isTotal && item.amount === 0
            const isLineItem = item.indentLevel === 1 && !item.isSubtotal && !item.isTotal

            return (
              <tr
                key={`${item.label}-${idx}`}
                className={`
                  ${item.isTotal ? 'border-t-2 border-double border-obsidian-500' : ''}
                  ${item.isSubtotal ? 'border-t border-obsidian-600' : ''}
                `}
              >
                <td
                  className={`
                    py-1.5 px-3
                    ${isSectionHeader ? 'font-serif font-semibold text-oatmeal-200 pt-4' : ''}
                    ${isLineItem ? 'pl-8 text-oatmeal-300 font-sans' : ''}
                    ${item.isSubtotal ? 'pl-8 font-sans font-medium text-oatmeal-200' : ''}
                    ${item.isTotal ? 'font-serif font-bold text-oatmeal-100' : ''}
                  `}
                >
                  <span>{item.label}</span>
                  {item.leadSheetRef && (
                    <span className="ml-2 text-[10px] text-oatmeal-600 font-mono">
                      [{item.leadSheetRef}]
                    </span>
                  )}
                </td>
                <td
                  className={`
                    py-1.5 px-3 text-right font-mono
                    ${isSectionHeader ? 'text-transparent' : ''}
                    ${isLineItem ? 'text-oatmeal-300' : ''}
                    ${item.isSubtotal ? 'font-medium text-oatmeal-200 border-t border-obsidian-600' : ''}
                    ${item.isTotal ? 'font-bold text-oatmeal-100' : ''}
                    ${!isSectionHeader && item.amount < 0 ? 'text-clay-400' : ''}
                  `}
                >
                  {isSectionHeader ? '' : formatCurrency(item.amount)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
