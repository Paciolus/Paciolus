"use client";

import { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useDiagnostic } from '@/contexts/DiagnosticContext';
import type { FluxItem, FluxSummary, ReconScore, ReconStats } from '@/types/diagnostic';
import { getRiskLevelClasses, type RiskLevel } from '@/utils/themeUtils';
import { formatCurrency, downloadBlob, apiDownload, apiPost } from '@/utils';

/** Browser-only expectation state for ISA 520 documentation */
interface ExpectationEntry {
    auditor_expectation: string;
    auditor_explanation: string;
}

/** API response type for flux analysis endpoint */
interface FluxAnalysisResponse {
    flux: {
        items: FluxItem[];
        summary: FluxSummary;
    };
    recon: {
        scores: ReconScore[];
        stats: ReconStats;
    };
}

export default function FluxPage() {
    const { token } = useAuth();
    const { result, setResult, isLoading, setIsLoading } = useDiagnostic();

    // Local state for files
    const [currentFile, setCurrentFile] = useState<File | null>(null);
    const [priorFile, setPriorFile] = useState<File | null>(null);
    const [threshold, setThreshold] = useState<number>(0);
    const [error, setError] = useState<string | null>(null);
    const [showExpectations, setShowExpectations] = useState(false);
    const [expectations, setExpectations] = useState<Record<string, ExpectationEntry>>({});

    const currentInputRef = useRef<HTMLInputElement>(null);
    const priorInputRef = useRef<HTMLInputElement>(null);

    const updateExpectation = useCallback((account: string, field: keyof ExpectationEntry, value: string) => {
        setExpectations(prev => ({
            ...prev,
            [account]: {
                ...prev[account] ?? { auditor_expectation: '', auditor_explanation: '' },
                [field]: value,
            },
        }));
    }, []);

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
            // Use apiPost with FormData - uses environment API_URL, not hardcoded localhost
            const response = await apiPost<FluxAnalysisResponse>(
                '/audit/flux',
                token,
                formData
            );

            if (!response.ok || !response.data) {
                throw new Error(response.error || "Failed to run analysis.");
            }

            setResult({
                flux: response.data.flux,
                recon: response.data.recon,
                filename: currentFile.name,
                uploadedAt: new Date().toISOString()
            });

        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : "Failed to run analysis.";
            setError(errorMessage);
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

    const handleExportExpectationsMemo = async () => {
        if (!result) return;

        const { blob, error: downloadError, ok } = await apiDownload(
            '/export/flux-expectations-memo',
            token,
            {
                method: 'POST',
                body: {
                    flux: result.flux,
                    expectations,
                    filename: result.filename,
                },
            }
        );

        if (!ok || !blob) {
            setError(`Export failed: ${downloadError || 'Unknown error'}`);
            return;
        }

        downloadBlob(blob, `FluxExpectations_${result.filename}.pdf`);
    };

    const flaggedItems = result?.flux.items.filter(
        item => item.risk_level === 'high' || item.risk_level === 'medium'
    ) ?? [];

    return (
        <div className="min-h-screen bg-surface-page text-content-primary p-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-7xl mx-auto"
            >
                <header className="mb-8">
                    <h1 className="text-3xl font-serif font-bold text-content-primary">Flux & Variance Intelligence</h1>
                    <p className="text-content-secondary mt-2 font-sans">Compare period-over-period changes and identify risks.</p>
                </header>

                {/* Input Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
 <div className="theme-card p-6">
                        <h3 className="font-serif font-semibold mb-4 text-sage-600">1. Current Period</h3>
                        <div
                            className="border-2 border-dashed border-theme rounded-lg p-8 text-center cursor-pointer hover:border-sage-500 transition-colors"
                            onClick={() => currentInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                hidden
                                ref={currentInputRef}
                                onChange={(e) => setCurrentFile(e.target.files?.[0] || null)}
                                accept=".csv,.xlsx,.xls"
                            />
                            <p className="text-sm font-sans text-content-secondary">{currentFile ? currentFile.name : "Select Trial Balance"}</p>
                        </div>
                    </div>

 <div className="theme-card p-6">
                        <h3 className="font-serif font-semibold mb-4 text-content-secondary">2. Prior Period</h3>
                        <div
                            className="border-2 border-dashed border-theme rounded-lg p-8 text-center cursor-pointer hover:border-sage-500 transition-colors"
                            onClick={() => priorInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                hidden
                                ref={priorInputRef}
                                onChange={(e) => setPriorFile(e.target.files?.[0] || null)}
                                accept=".csv,.xlsx,.xls"
                            />
                            <p className="text-sm font-sans text-content-secondary">{priorFile ? priorFile.name : "Select Prior TB"}</p>
                        </div>
                    </div>

 <div className="theme-card p-6 flex flex-col justify-between">
                        <div>
                            <h3 className="font-serif font-semibold mb-4 text-content-secondary">3. Parameters</h3>
                            <label htmlFor="flux-materiality-threshold" className="block text-sm mb-2 text-content-secondary font-sans">Materiality Threshold ($)</label>
                            <input
                                id="flux-materiality-threshold"
                                type="number"
                                className="w-full bg-surface-input border border-theme rounded-lg p-3 text-content-primary font-mono focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent transition-all"
                                value={threshold}
                                onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
                            />
                        </div>
                        <button
                            onClick={handleRunAnalysis}
                            disabled={isLoading}
                            className={`w-full py-3 rounded-xl font-sans font-bold mt-6 transition-colors ${isLoading
                                    ? "bg-surface-card-secondary cursor-not-allowed text-content-tertiary"
                                    : "bg-sage-600 hover:bg-sage-700 text-white"
                                }`}
                        >
                            {isLoading ? "Processing..." : "Run Analysis"}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-clay-50 border border-clay-200 text-clay-600 p-4 rounded-xl mb-8 font-sans">
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
                            <h2 className="text-2xl font-serif font-bold text-content-primary">Flux Analysis</h2>
                            <button
                                onClick={handleExport}
                                className="bg-surface-card hover:bg-surface-card-secondary px-4 py-2 rounded-lg text-sm font-sans text-content-primary border border-theme transition-colors"
                            >
                                Export Lead Sheets (Excel)
                            </button>
                        </div>

 <div className="theme-card overflow-hidden max-h-[600px] overflow-y-auto">
                            <table className="w-full text-left text-sm font-sans">
                                <thead className="bg-surface-card-secondary text-content-secondary sticky top-0">
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
                                <tbody className="divide-y divide-theme-divider">
                                    {result.flux.items.map((item) => (
                                        <tr key={`${item.account}-${item.type || 'flux'}`} className="hover:bg-surface-card-secondary">
                                            <td className="p-4 font-medium text-content-primary">{item.account}</td>
                                            <td className="p-4 text-right text-content-secondary font-mono">{formatCurrency(item.prior, true)}</td>
                                            <td className="p-4 text-right font-mono">{formatCurrency(item.current, true)}</td>
                                            <td className={`p-4 text-right font-mono ${item.delta_amount < 0 ? 'text-clay-600' : 'text-sage-600'}`}>
                                                {formatCurrency(item.delta_amount, true)}
                                            </td>
                                            <td className="p-4 text-right font-mono">{item.display_percent}</td>
                                            <td className="p-4 text-center">
                                                <RiskBadge level={item.risk_level as RiskLevel} />
                                            </td>
                                            <td className="p-4 text-content-tertiary text-xs">
                                                {item.variance_indicators.join(", ")}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {/* ISA 520 Expectation Documentation */}
                        {flaggedItems.length > 0 && (
                            <div className="theme-card overflow-hidden">
                                <button
                                    onClick={() => setShowExpectations(e => !e)}
                                    className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-card-secondary transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <h3 className="font-serif text-sm text-content-primary">ISA 520 Expectation Documentation</h3>
                                        <span className="px-2 py-0.5 rounded-full bg-oatmeal-50 border border-oatmeal-200 text-xs font-mono text-content-secondary">
                                            {flaggedItems.length} flagged items
                                        </span>
                                    </div>
                                    <svg
                                        className={`w-5 h-5 text-content-tertiary transform transition-transform ${showExpectations ? 'rotate-180' : ''}`}
                                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                {showExpectations && (
                                    <div className="border-t border-theme">
                                        {/* Disclaimer */}
                                        <div className="px-6 py-3 bg-oatmeal-50 border-b border-theme">
                                            <p className="text-xs font-sans text-content-secondary">
                                                Practitioner-documented expectations — not generated by Paciolus. ISA 520 requires the auditor to develop expectations before comparing to recorded amounts.
                                            </p>
                                        </div>

                                        {/* Expectation fields per flagged item */}
                                        <div className="divide-y divide-theme-divider">
                                            {flaggedItems.map((item) => {
                                                const exp = expectations[item.account] ?? { auditor_expectation: '', auditor_explanation: '' };
                                                return (
                                                    <div key={item.account} className="px-6 py-4">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <span className="font-sans text-sm font-medium text-content-primary">{item.account}</span>
                                                            <RiskBadge level={item.risk_level as RiskLevel} />
                                                            <span className="font-mono text-xs text-content-tertiary">
                                                                {formatCurrency(item.delta_amount, true)} ({item.display_percent})
                                                            </span>
                                                        </div>
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                            <div>
                                                                <label className="block text-xs font-sans text-content-secondary mb-1">
                                                                    Practitioner Expectation
                                                                </label>
                                                                <textarea
                                                                    rows={2}
                                                                    className="w-full bg-surface-input border border-theme rounded-lg p-2 text-xs font-sans text-content-primary focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent placeholder:text-content-tertiary"
                                                                    placeholder="What did you expect for this account?"
                                                                    value={exp.auditor_expectation}
                                                                    onChange={(e) => updateExpectation(item.account, 'auditor_expectation', e.target.value)}
                                                                />
                                                            </div>
                                                            <div>
                                                                <label className="block text-xs font-sans text-content-secondary mb-1">
                                                                    Explanation of Variance
                                                                </label>
                                                                <textarea
                                                                    rows={2}
                                                                    className="w-full bg-surface-input border border-theme rounded-lg p-2 text-xs font-sans text-content-primary focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent placeholder:text-content-tertiary"
                                                                    placeholder="Why does the recorded amount differ from expectation?"
                                                                    value={exp.auditor_explanation}
                                                                    onChange={(e) => updateExpectation(item.account, 'auditor_explanation', e.target.value)}
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>

                                        {/* Export button */}
                                        <div className="px-6 py-3 border-t border-theme">
                                            <button
                                                onClick={handleExportExpectationsMemo}
                                                className="px-4 py-2 text-xs font-sans rounded-lg border border-theme bg-surface-card-secondary text-content-secondary hover:bg-oatmeal-100 transition-colors"
                                            >
                                                Export Expectations Memo (PDF)
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </motion.div>
        </div>
    );
}

function SummaryCard({ label, value, variant = "default" }: { label: string, value: string | number, variant?: "default" | "danger" | "warning" }) {
    const colorClass = variant === "danger" ? "text-clay-600"
        : variant === "warning" ? "text-content-secondary"
        : "text-content-primary";

    return (
 <div className="theme-card p-4">
            <div className="text-content-tertiary text-sm mb-1 font-sans">{label}</div>
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
