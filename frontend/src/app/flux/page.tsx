"use client";

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { useDiagnostic } from '@/context/DiagnosticContext';
import { useAuth } from '@/context/AuthContext';
import { formatCurrency, downloadBlob, apiDownload } from '@/utils';
import { getRiskLevelClasses, type RiskLevel } from '@/utils/themeUtils';

export default function FluxPage() {
    const { token } = useAuth();
    const { result, setResult, isLoading, setIsLoading } = useDiagnostic();

    // Local state for files
    const [currentFile, setCurrentFile] = useState<File | null>(null);
    const [priorFile, setPriorFile] = useState<File | null>(null);
    const [threshold, setThreshold] = useState<number>(0);
    const [error, setError] = useState<string | null>(null);

    const currentInputRef = useRef<HTMLInputElement>(null);
    const priorInputRef = useRef<HTMLInputElement>(null);

    const handleRunAnalysis = async () => {
        if (!currentFile || !priorFile) {
            setError("Please select both Current and Prior period files.");
            return;
        }
        setError(null);
        setIsLoading(true);

        const formData = new FormData();
        formData.append("current_file", currentFile);
        formData.append("prior_file", priorFile);
        formData.append("materiality", threshold.toString());

        try {
            const response = await fetch("http://localhost:8000/diagnostics/flux", {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            const data = await response.json();
            setResult({
                flux: data.flux,
                recon: data.recon,
                filename: currentFile.name,
                uploadedAt: new Date().toISOString()
            });

        } catch (err: any) {
            setError(err.message || "Failed to run analysis.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleExport = async () => {
        if (!result) return;

        const { blob, error: downloadError, ok } = await apiDownload(
            '/export/leadsheets',
            token,
            {
                method: 'POST',
                body: {
                    flux: result.flux,
                    recon: result.recon,
                    filename: result.filename
                }
            }
        );

        if (!ok || !blob) {
            setError(`Export failed: ${downloadError || 'Unknown error'}`);
            return;
        }

        downloadBlob(blob, `LeadSheets_${result.filename}.xlsx`);
    };

    return (
        <div className="min-h-screen bg-gradient-obsidian text-oatmeal-200 p-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-7xl mx-auto"
            >
                <header className="mb-8">
                    <h1 className="text-3xl font-serif font-bold text-oatmeal-100">Flux & Variance Intelligence</h1>
                    <p className="text-oatmeal-400 mt-2 font-sans">Compare period-over-period changes and identify risks.</p>
                </header>

                {/* Input Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-obsidian-700 p-6 rounded-xl border border-obsidian-500">
                        <h3 className="font-serif font-semibold mb-4 text-sage-400">1. Current Period</h3>
                        <div
                            className="border-2 border-dashed border-obsidian-500 rounded-lg p-8 text-center cursor-pointer hover:border-sage-500 transition-colors"
                            onClick={() => currentInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                hidden
                                ref={currentInputRef}
                                onChange={(e) => setCurrentFile(e.target.files?.[0] || null)}
                                accept=".csv,.xlsx,.xls"
                            />
                            <p className="text-sm font-sans text-oatmeal-300">{currentFile ? currentFile.name : "Select Trial Balance"}</p>
                        </div>
                    </div>

                    <div className="bg-obsidian-700 p-6 rounded-xl border border-obsidian-500">
                        <h3 className="font-serif font-semibold mb-4 text-oatmeal-300">2. Prior Period</h3>
                        <div
                            className="border-2 border-dashed border-obsidian-500 rounded-lg p-8 text-center cursor-pointer hover:border-oatmeal-400 transition-colors"
                            onClick={() => priorInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                hidden
                                ref={priorInputRef}
                                onChange={(e) => setPriorFile(e.target.files?.[0] || null)}
                                accept=".csv,.xlsx,.xls"
                            />
                            <p className="text-sm font-sans text-oatmeal-300">{priorFile ? priorFile.name : "Select Prior TB"}</p>
                        </div>
                    </div>

                    <div className="bg-obsidian-700 p-6 rounded-xl border border-obsidian-500 flex flex-col justify-between">
                        <div>
                            <h3 className="font-serif font-semibold mb-4 text-oatmeal-400">3. Parameters</h3>
                            <label className="block text-sm mb-2 text-oatmeal-400 font-sans">Materiality Threshold ($)</label>
                            <input
                                type="number"
                                className="w-full bg-obsidian-800 border border-obsidian-500 rounded-lg p-3 text-oatmeal-200 font-mono focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent transition-all"
                                value={threshold}
                                onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
                            />
                        </div>
                        <button
                            onClick={handleRunAnalysis}
                            disabled={isLoading}
                            className={`w-full py-3 rounded-xl font-sans font-bold mt-6 transition-all ${isLoading
                                    ? "bg-obsidian-600 cursor-not-allowed text-oatmeal-500"
                                    : "bg-sage-500 hover:bg-sage-400 text-oatmeal-50"
                                }`}
                        >
                            {isLoading ? "Processing..." : "Run Analysis"}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-clay-500/20 border border-clay-500/40 text-clay-300 p-4 rounded-xl mb-8 font-sans">
                        {error}
                    </div>
                )}

                {/* Results Section */}
                {result && (
                    <div className="space-y-8">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <SummaryCard label="Total Items" value={result.flux.summary.total_items} />
                            <SummaryCard label="High Risk Items" value={result.flux.summary.high_risk_count} variant="danger" />
                            <SummaryCard label="New Accounts" value={result.flux.summary.new_accounts} />
                            <SummaryCard label="Recon High Risk" value={result.recon.stats.high} variant="warning" />
                        </div>

                        <div className="flex justify-between items-center">
                            <h2 className="text-2xl font-serif font-bold text-oatmeal-100">Flux Analysis</h2>
                            <button
                                onClick={handleExport}
                                className="bg-obsidian-600 hover:bg-obsidian-500 px-4 py-2 rounded-lg text-sm font-sans text-oatmeal-200 border border-obsidian-500 transition-colors"
                            >
                                Export Lead Sheets (Excel)
                            </button>
                        </div>

                        <div className="bg-obsidian-700 rounded-xl overflow-hidden border border-obsidian-500 max-h-[600px] overflow-y-auto">
                            <table className="w-full text-left text-sm font-sans">
                                <thead className="bg-obsidian-800 text-oatmeal-400 sticky top-0">
                                    <tr>
                                        <th className="p-4">Account</th>
                                        <th className="p-4 text-right">Prior</th>
                                        <th className="p-4 text-right">Current</th>
                                        <th className="p-4 text-right">Delta</th>
                                        <th className="p-4 text-right">%</th>
                                        <th className="p-4 text-center">Risk</th>
                                        <th className="p-4">Reason</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-obsidian-600">
                                    {result.flux.items.map((item) => (
                                        <tr key={`${item.account}-${item.type || 'flux'}`} className="hover:bg-obsidian-600/50">
                                            <td className="p-4 font-medium text-oatmeal-200">{item.account}</td>
                                            <td className="p-4 text-right text-oatmeal-400 font-mono">{formatCurrency(item.prior, true)}</td>
                                            <td className="p-4 text-right font-mono">{formatCurrency(item.current, true)}</td>
                                            <td className={`p-4 text-right font-mono ${item.delta_amount < 0 ? 'text-clay-400' : 'text-sage-400'}`}>
                                                {formatCurrency(item.delta_amount, true)}
                                            </td>
                                            <td className="p-4 text-right font-mono">{item.display_percent}</td>
                                            <td className="p-4 text-center">
                                                <RiskBadge level={item.risk_level as RiskLevel} />
                                            </td>
                                            <td className="p-4 text-oatmeal-500 text-xs">
                                                {item.risk_reasons.join(", ")}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </motion.div>
        </div>
    );
}

function SummaryCard({ label, value, variant = "default" }: { label: string, value: string | number, variant?: "default" | "danger" | "warning" }) {
    const colorClass = variant === "danger" ? "text-clay-400"
        : variant === "warning" ? "text-oatmeal-400"
        : "text-oatmeal-100";

    return (
        <div className="bg-obsidian-700 p-4 rounded-xl border border-obsidian-500">
            <div className="text-oatmeal-500 text-sm mb-1 font-sans">{label}</div>
            <div className={`text-2xl font-mono font-bold ${colorClass}`}>{value}</div>
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
