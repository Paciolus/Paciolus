"use client";

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { useDiagnostic } from '@/context/DiagnosticContext';
import { useAuth } from '@/context/AuthContext';
import { formatCurrency, downloadBlob, apiDownload } from '@/utils';

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
        <div className="min-h-screen bg-neutral-900 text-stone-200 p-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-7xl mx-auto"
            >
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-stone-100">Flux & Variance Intelligence</h1>
                    <p className="text-stone-400 mt-2">Compare period-over-period changes and identify risks.</p>
                </header>

                {/* Input Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-neutral-800 p-6 rounded-lg border border-neutral-700">
                        <h3 className="font-semibold mb-4 text-emerald-400">1. Current Period</h3>
                        <div
                            className="border-2 border-dashed border-neutral-600 rounded-md p-8 text-center cursor-pointer hover:border-emerald-500 transition-colors"
                            onClick={() => currentInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                hidden
                                ref={currentInputRef}
                                onChange={(e) => setCurrentFile(e.target.files?.[0] || null)}
                                accept=".csv,.xlsx,.xls"
                            />
                            <p className="text-sm">{currentFile ? currentFile.name : "Select Trial Balance"}</p>
                        </div>
                    </div>

                    <div className="bg-neutral-800 p-6 rounded-lg border border-neutral-700">
                        <h3 className="font-semibold mb-4 text-blue-400">2. Prior Period</h3>
                        <div
                            className="border-2 border-dashed border-neutral-600 rounded-md p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
                            onClick={() => priorInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                hidden
                                ref={priorInputRef}
                                onChange={(e) => setPriorFile(e.target.files?.[0] || null)}
                                accept=".csv,.xlsx,.xls"
                            />
                            <p className="text-sm">{priorFile ? priorFile.name : "Select Prior TB"}</p>
                        </div>
                    </div>

                    <div className="bg-neutral-800 p-6 rounded-lg border border-neutral-700 flex flex-col justify-between">
                        <div>
                            <h3 className="font-semibold mb-4 text-amber-400">3. Parameters</h3>
                            <label className="block text-sm mb-2 text-stone-400">Materiality Threshold ($)</label>
                            <input
                                type="number"
                                className="w-full bg-neutral-900 border border-neutral-600 rounded p-2 text-white"
                                value={threshold}
                                onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
                            />
                        </div>
                        <button
                            onClick={handleRunAnalysis}
                            disabled={isLoading}
                            className={`w-full py-3 rounded font-bold mt-6 ${isLoading
                                    ? "bg-neutral-600 cursor-not-allowed"
                                    : "bg-emerald-600 hover:bg-emerald-500 text-white"
                                }`}
                        >
                            {isLoading ? "Processing..." : "Run Analysis"}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-900/30 border border-red-800 text-red-200 p-4 rounded mb-8">
                        {error}
                    </div>
                )}

                {/* Results Section */}
                {result && (
                    <div className="space-y-8">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <SummaryCard label="Total Items" value={result.flux.summary.total_items} />
                            <SummaryCard label="High Risk Items" value={result.flux.summary.high_risk_count} color="text-red-400" />
                            <SummaryCard label="New Accounts" value={result.flux.summary.new_accounts} />
                            <SummaryCard label="Recon High Risk" value={result.recon.stats.high} color="text-amber-400" />
                        </div>

                        <div className="flex justify-between items-center">
                            <h2 className="text-2xl font-bold">Flux Analysis</h2>
                            <button
                                onClick={handleExport}
                                className="bg-stone-700 hover:bg-stone-600 px-4 py-2 rounded text-sm"
                            >
                                Export Lead Sheets (Excel)
                            </button>
                        </div>

                        <div className="bg-neutral-800 rounded-lg overflow-hidden border border-neutral-700 max-h-[600px] overflow-y-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-neutral-900 text-stone-400 sticky top-0">
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
                                <tbody className="divide-y divide-neutral-700">
                                    {result.flux.items.map((item) => (
                                        <tr key={`${item.account}-${item.type || 'flux'}`} className="hover:bg-neutral-700/50">
                                            <td className="p-4 font-medium">{item.account}</td>
                                            <td className="p-4 text-right text-stone-400">{formatCurrency(item.prior, true)}</td>
                                            <td className="p-4 text-right">{formatCurrency(item.current, true)}</td>
                                            <td className={`p-4 text-right ${item.delta_amount < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                                {formatCurrency(item.delta_amount, true)}
                                            </td>
                                            <td className="p-4 text-right">{item.display_percent}</td>
                                            <td className="p-4 text-center">
                                                <RiskBadge level={item.risk_level} />
                                            </td>
                                            <td className="p-4 text-stone-400 text-xs">
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

function SummaryCard({ label, value, color = "text-white" }: { label: string, value: string | number, color?: string }) {
    return (
        <div className="bg-neutral-800 p-4 rounded border border-neutral-700">
            <div className="text-stone-500 text-sm mb-1">{label}</div>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
        </div>
    );
}

function RiskBadge({ level }: { level: string }) {
    const colors: Record<string, string> = {
        high: "bg-red-900/50 text-red-200 border-red-800",
        medium: "bg-amber-900/50 text-amber-200 border-amber-800",
        low: "bg-emerald-900/50 text-emerald-200 border-emerald-800",
        none: "bg-neutral-700 text-neutral-400 border-neutral-600"
    };
    return (
        <span className={`px-2 py-1 rounded text-xs border ${colors[level] || colors.none}`}>
            {level.toUpperCase()}
        </span>
    );
}

