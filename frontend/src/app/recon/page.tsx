"use client";

import { motion } from 'framer-motion';
import { useDiagnostic } from '@/context/DiagnosticContext';
import Link from 'next/link';

export default function ReconPage() {
    const { result } = useDiagnostic();

    if (!result) {
        return (
            <div className="min-h-screen bg-neutral-900 text-stone-200 p-8 flex flex-col items-center justify-center">
                <h2 className="text-xl font-bold text-stone-400 mb-4">No Analysis Data Found</h2>
                <p className="mb-6">Please run a Flux Analysis first to generate reconciliation scores.</p>
                <Link href="/flux" className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded">
                    Go to Flux Analysis
                </Link>
            </div>
        );
    }

    // Sort scores by risk (High -> Low)
    const scores = [...result.recon.scores].sort((a, b) => b.score - a.score);

    return (
        <div className="min-h-screen bg-neutral-900 text-stone-200 p-8">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-7xl mx-auto"
            >
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-stone-100">Reconciliation Intelligence</h1>
                        <p className="text-stone-400 mt-2">Prioritize account reconciliations based on risk factors.</p>
                    </div>
                    <Link href="/flux" className="text-emerald-400 hover:text-emerald-300">
                        ← Back to Flux
                    </Link>
                </header>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-neutral-800 p-6 rounded-lg border-l-4 border-red-500">
                        <h3 className="text-stone-400 text-sm">High Risk Accounts</h3>
                        <div className="text-3xl font-bold text-white mt-2">{result.recon.stats.high}</div>
                        <p className="text-xs text-stone-500 mt-1">Require detailed evidence</p>
                    </div>
                    <div className="bg-neutral-800 p-6 rounded-lg border-l-4 border-amber-500">
                        <h3 className="text-stone-400 text-sm">Medium Risk Accounts</h3>
                        <div className="text-3xl font-bold text-white mt-2">{result.recon.stats.medium}</div>
                        <p className="text-xs text-stone-500 mt-1">Standard review needed</p>
                    </div>
                    <div className="bg-neutral-800 p-6 rounded-lg border-l-4 border-emerald-500">
                        <h3 className="text-stone-400 text-sm">Low Risk Accounts</h3>
                        <div className="text-3xl font-bold text-white mt-2">{result.recon.stats.low}</div>
                        <p className="text-xs text-stone-500 mt-1">Automated/Batch approval</p>
                    </div>
                </div>

                {/* Grid */}
                <div className="bg-neutral-800 rounded-lg overflow-hidden border border-neutral-700">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-neutral-900 text-stone-400">
                            <tr>
                                <th className="p-4">Account</th>
                                <th className="p-4 text-center">Score</th>
                                <th className="p-4 text-center">Band</th>
                                <th className="p-4">Risk Factors</th>
                                <th className="p-4">Suggested Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-neutral-700">
                            {scores.map((item) => (
                                <tr key={item.account} className="hover:bg-neutral-700/50">
                                    <td className="p-4 font-medium">{item.account}</td>
                                    <td className="p-4 text-center font-mono font-bold">{item.score}</td>
                                    <td className="p-4 text-center">
                                        <span className={`px-2 py-1 rounded text-xs border ${item.band === 'high' ? 'bg-red-900/50 text-red-200 border-red-800' :
                                                item.band === 'medium' ? 'bg-amber-900/50 text-amber-200 border-amber-800' :
                                                    'bg-emerald-900/50 text-emerald-200 border-emerald-800'
                                            }`}>
                                            {item.band.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex flex-wrap gap-2">
                                            {item.factors.map((f, i) => (
                                                <span key={`${item.account}-factor-${i}`} className="px-2 py-0.5 bg-neutral-900 text-stone-400 text-xs rounded border border-neutral-700">
                                                    {f}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="p-4 text-stone-300">
                                        {item.action}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </motion.div>
        </div>
    );
}
