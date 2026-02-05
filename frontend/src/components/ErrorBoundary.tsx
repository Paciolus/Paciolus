'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary component to catch JavaScript errors in child components.
 *
 * Prevents the entire application from crashing when a component throws an error.
 * Displays a graceful fallback UI instead of a white screen of death.
 *
 * Sprint 25: Stability improvement per QualityGuardian recommendation.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI with Oat & Obsidian styling
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="card max-w-md w-full text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-500/20 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-clay-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>

            <h2 className="text-xl font-serif font-bold text-oatmeal-200 mb-2">
              Something went wrong
            </h2>

            <p className="text-oatmeal-400 mb-6">
              An unexpected error occurred. Your data has not been affected.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-obsidian-800 rounded-lg text-left">
                <p className="text-xs font-mono text-clay-300 break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="btn-primary"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="btn-secondary"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Feature-specific error boundary with custom messaging.
 * Use this for wrapping specific sections of the app.
 */
export function FeatureErrorBoundary({
  children,
  featureName = 'This feature'
}: {
  children: ReactNode;
  featureName?: string;
}) {
  return (
    <ErrorBoundary
      fallback={
        <div className="p-6 bg-obsidian-700/50 rounded-xl border border-clay-500/20">
          <div className="flex items-center gap-3 text-clay-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm">
              {featureName} encountered an error. Please refresh the page.
            </span>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

export default ErrorBoundary;
