"use client";

import { motion } from 'framer-motion';
import { useDiagnostic } from '@/context/DiagnosticContext';
import Link from 'next/link';
import { getRiskLevelClasses, type RiskLevel } from '@/utils/themeUtils';

export default function ReconPage() {
    const { result } = useDiagnostic();

    if (!result) {
        return (
            <div className="min-h-screen bg-gradient-obsidian text-oatmeal-200 p-8 flex flex-col items-center justify-center">
                <h2 className="text-xl font-serif font-bold text-oatmeal-400 mb-4">No Analysis Data Found</h2>
                <p className="mb-6 font-sans text-oatmeal-300">Please run a Flux Analysis first to generate reconciliation scores.</p>
                <Link href="/flux" className="bg-sage-500 hover:bg-sage-400 text-oatmeal-50 px-6 py-3 rounded-xl font-sans font-bold transition-colors">
                    Go to Flux Analysis
                </Link>
            </div>
        );
    }

    // Sort scores by risk (High -> Low)
    const scores = [...result.recon.scores].sort((a, b) => b.score - a.score);

    return (
        <div className="min-h-screen bg-gradient-obsidian text-oatmeal-200 p-8">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-7xl mx-auto"
            >
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-serif font-bold text-oatmeal-100">Reconciliation Intelligence</h1>
                        <p className="text-oatmeal-400 mt-2 font-sans">Prioritize account reconciliations based on risk factors.</p>
                    </div>
                    <Link href="/flux" className="text-sage-400 hover:text-sage-300 font-sans transition-colors">
                        ← Back to Flux
                    </Link>
                </header>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-obsidian-700 p-6 rounded-xl border-l-4 border-clay-500">
                        <h3 className="text-oatmeal-400 text-sm font-sans">High Risk Accounts</h3>
                        <div className="text-3xl font-mono font-bold text-oatmeal-100 mt-2">{result.recon.stats.high}</div>
                        <p className="text-xs text-oatmeal-500 mt-1 font-sans">Require detailed evidence</p>
                    </div>
                    <div className="bg-obsidian-700 p-6 rounded-xl border-l-4 border-oatmeal-400">
                        <h3 className="text-oatmeal-400 text-sm font-sans">Medium Risk Accounts</h3>
                        <div className="text-3xl font-mono font-bold text-oatmeal-100 mt-2">{result.recon.stats.medium}</div>
                        <p className="text-xs text-oatmeal-500 mt-1 font-sans">Standard review needed</p>
                    </div>
                    <div className="bg-obsidian-700 p-6 rounded-xl border-l-4 border-sage-500">
                        <h3 className="text-oatmeal-400 text-sm font-sans">Low Risk Accounts</h3>
                        <div className="text-3xl font-mono font-bold text-oatmeal-100 mt-2">{result.recon.stats.low}</div>
                        <p className="text-xs text-oatmeal-500 mt-1 font-sans">Automated/Batch approval</p>
                    </div>
                </div>

                {/* Grid */}
                <div className="bg-obsidian-700 rounded-xl overflow-hidden border border-obsidian-500">
                    <table className="w-full text-left text-sm font-sans">
                        <thead className="bg-obsidian-800 text-oatmeal-400">
                            <tr>
                                <th className="p-4">Account</th>
                                <th className="p-4 text-center">Score</th>
                                <th className="p-4 text-center">Band</th>
                                <th className="p-4">Risk Factors</th>
                                <th className="p-4">Suggested Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-obsidian-600">
                            {scores.map((item) => (
                                <tr key={item.account} className="hover:bg-obsidian-600/50">
                                    <td className="p-4 font-medium text-oatmeal-200">{item.account}</td>
                                    <td className="p-4 text-center font-mono font-bold text-oatmeal-100">{item.score}</td>
                                    <td className="p-4 text-center">
                                        <RiskBadge level={item.band as RiskLevel} />
                                    </td>
                                    <td className="p-4">
                                        <div className="flex flex-wrap gap-2">
                                            {item.factors.map((f, i) => (
                                                <span key={`${item.account}-factor-${i}`} className="px-2 py-0.5 bg-obsidian-800 text-oatmeal-400 text-xs rounded border border-obsidian-600 font-sans">
                                                    {f}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="p-4 text-oatmeal-300">
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

function RiskBadge({ level }: { level: RiskLevel }) {
    const classes = getRiskLevelClasses(level);
    return (
        <span className={`px-2 py-1 rounded text-xs font-sans font-medium border ${classes}`}>
            {level.toUpperCase()}
        </span>
    );
}
