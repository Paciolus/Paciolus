"use client";

import Link from 'next/link';
import { motion } from 'framer-motion';
import { useDiagnostic } from '@/contexts/DiagnosticContext';
import { getRiskLevelClasses, type RiskLevel } from '@/utils/themeUtils';

export default function ReconPage() {
    const { result } = useDiagnostic();

    if (!result) {
        return (
            <div className="min-h-screen bg-surface-page text-content-primary p-8 flex flex-col items-center justify-center">
                <h2 className="text-xl font-serif font-bold text-content-secondary mb-4">No Analysis Data Found</h2>
                <p className="mb-6 font-sans text-content-secondary">Please run a Flux Analysis first to generate reconciliation scores.</p>
                <Link href="/flux" className="bg-sage-600 hover:bg-sage-700 text-white px-6 py-3 rounded-xl font-sans font-bold transition-colors">
                    Go to Flux Analysis
                </Link>
            </div>
        );
    }

    // Sort scores by risk (High -> Low)
    const scores = [...result.recon.scores].sort((a, b) => b.score - a.score);

    return (
        <div className="min-h-screen bg-surface-page text-content-primary p-8">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-7xl mx-auto"
            >
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-serif font-bold text-content-primary">Reconciliation Intelligence</h1>
                        <p className="text-content-secondary mt-2 font-sans">Prioritize account reconciliations based on risk factors.</p>
                    </div>
                    <Link href="/flux" className="text-sage-600 hover:text-sage-700 font-sans transition-colors">
                        ← Back to Flux
                    </Link>
                </header>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-surface-card p-6 rounded-xl border-l-4 border-clay-500 shadow-theme-card">
                        <h3 className="text-content-secondary text-sm font-sans">High Risk Accounts</h3>
                        <div className="text-3xl font-mono font-bold text-content-primary mt-2">{result.recon.stats.high}</div>
                        <p className="text-xs text-content-tertiary mt-1 font-sans">Require detailed evidence</p>
                    </div>
                    <div className="bg-surface-card p-6 rounded-xl border-l-4 border-oatmeal-400 shadow-theme-card">
                        <h3 className="text-content-secondary text-sm font-sans">Medium Risk Accounts</h3>
                        <div className="text-3xl font-mono font-bold text-content-primary mt-2">{result.recon.stats.medium}</div>
                        <p className="text-xs text-content-tertiary mt-1 font-sans">Standard review needed</p>
                    </div>
                    <div className="bg-surface-card p-6 rounded-xl border-l-4 border-sage-500 shadow-theme-card">
                        <h3 className="text-content-secondary text-sm font-sans">Low Risk Accounts</h3>
                        <div className="text-3xl font-mono font-bold text-content-primary mt-2">{result.recon.stats.low}</div>
                        <p className="text-xs text-content-tertiary mt-1 font-sans">Automated/Batch approval</p>
                    </div>
                </div>

                {/* Grid */}
 <div className="theme-card overflow-hidden">
                    <table className="w-full text-left text-sm font-sans">
                        <thead className="bg-surface-card-secondary text-content-secondary">
                            <tr>
                                <th className="p-4">Account</th>
                                <th className="p-4 text-center">Score</th>
                                <th className="p-4 text-center">Band</th>
                                <th className="p-4">Risk Factors</th>
                                <th className="p-4">Suggested Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-theme-divider">
                            {scores.map((item) => (
                                <tr key={item.account} className="hover:bg-surface-card-secondary">
                                    <td className="p-4 font-medium text-content-primary">{item.account}</td>
                                    <td className="p-4 text-center font-mono font-bold text-content-primary">{item.score}</td>
                                    <td className="p-4 text-center">
                                        <RiskBadge level={item.band as RiskLevel} />
                                    </td>
                                    <td className="p-4">
                                        <div className="flex flex-wrap gap-2">
                                            {item.factors.map((f, i) => (
                                                <span key={`${item.account}-factor-${i}`} className="px-2 py-0.5 bg-surface-card-secondary text-content-secondary text-xs rounded border border-theme font-sans">
                                                    {f}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="p-4 text-content-secondary">
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
