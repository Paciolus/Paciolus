import { formatCurrency } from '@/utils'
import type { CashFlowStatement } from './types'

export function CashFlowTable({ cashFlow }: { cashFlow: CashFlowStatement }) {
  return (
    <div className="overflow-x-auto space-y-4">
      {[cashFlow.operating, cashFlow.investing, cashFlow.financing].map(section => (
        <div key={section.label}>
          <div className="font-serif text-oatmeal-200 text-sm font-medium mb-2 pt-2">{section.label}</div>
          <table className="w-full text-sm mb-1">
            <tbody>
              {section.items.map((item, idx) => (
                <tr key={`${item.label}-${idx}`}>
                  <td className="py-1 px-3 pl-8 text-oatmeal-300 font-sans">
                    {item.label}
                    {item.source && (
                      <span className="ml-2 text-[10px] text-oatmeal-600 font-mono">[{item.source}]</span>
                    )}
                  </td>
                  <td className={`py-1 px-3 text-right font-mono w-40 ${item.amount < 0 ? 'text-clay-400' : 'text-oatmeal-300'}`}>
                    {formatCurrency(item.amount)}
                  </td>
                </tr>
              ))}
              <tr className="border-t border-obsidian-600">
                <td className="py-1.5 px-3 pl-8 font-sans font-medium text-oatmeal-200">
                  Net {section.label.replace('Cash Flows from ', '')}
                </td>
                <td className={`py-1.5 px-3 text-right font-mono font-medium w-40 ${section.subtotal < 0 ? 'text-clay-400' : 'text-oatmeal-200'}`}>
                  {formatCurrency(section.subtotal)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}

      {/* Net Change */}
      <div className="border-t-2 border-double border-obsidian-500 pt-2">
        <table className="w-full text-sm">
          <tbody>
            <tr>
              <td className="py-1.5 px-3 font-serif font-bold text-oatmeal-100">NET CHANGE IN CASH</td>
              <td className={`py-1.5 px-3 text-right font-mono font-bold w-40 ${cashFlow.netChange < 0 ? 'text-clay-400' : 'text-oatmeal-100'}`}>
                {formatCurrency(cashFlow.netChange)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Reconciliation */}
      {cashFlow.hasPriorPeriod && (
        <div className="pt-2">
          <table className="w-full text-sm">
            <tbody>
              <tr>
                <td className="py-1 px-3 text-oatmeal-300 font-sans">Beginning Cash</td>
                <td className="py-1 px-3 text-right font-mono text-oatmeal-300 w-40">{formatCurrency(cashFlow.beginningCash)}</td>
              </tr>
              <tr>
                <td className="py-1 px-3 text-oatmeal-300 font-sans">Net Change in Cash</td>
                <td className="py-1 px-3 text-right font-mono text-oatmeal-300 w-40">{formatCurrency(cashFlow.netChange)}</td>
              </tr>
              <tr className="border-t-2 border-double border-obsidian-500">
                <td className="py-1.5 px-3 font-serif font-bold text-oatmeal-100">Ending Cash</td>
                <td className="py-1.5 px-3 text-right font-mono font-bold text-oatmeal-100 w-40">{formatCurrency(cashFlow.endingCash)}</td>
              </tr>
            </tbody>
          </table>

          <div className="mt-3 flex justify-center">
            {cashFlow.isReconciled ? (
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-sage-500/20 text-sage-400 border border-sage-500/30">
                RECONCILED
              </span>
            ) : (
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-clay-500/20 text-clay-400 border border-clay-500/30">
                UNRECONCILED ({formatCurrency(cashFlow.reconciliationDifference)})
              </span>
            )}
          </div>
        </div>
      )}

      {/* Notes */}
      {cashFlow.notes.length > 0 && (
        <div className="pt-2 space-y-1">
          {cashFlow.notes.map((note, idx) => (
            <p key={idx} className="text-xs text-oatmeal-500 font-sans italic">
              Note: {note}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
