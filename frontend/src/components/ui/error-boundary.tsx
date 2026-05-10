'use client';

/**
 * React Error Boundaries
 * 
 * Production-grade error handling with:
 * - Global error boundary (catches all unhandled errors)
 * - Section-level boundaries (isolate failures to components)
 * - Error reporting to backend analytics
 * - User-friendly fallback UIs
 * - Retry mechanism
 * - Development-mode error details
 */

import React, { Component, ErrorInfo, ReactNode, useCallback, useState } from 'react';
import { motion } from 'framer-motion';

// ─── Error Reporting ───────────────────────────────────────────────────────

interface ErrorReport {
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  timestamp: string;
  userAgent: string;
}

async function reportError(report: ErrorReport): Promise<void> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    await fetch(`${apiUrl}/api/v1/analytics/pageview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: `/error/${encodeURIComponent(report.message.slice(0, 100))}`,
        referrer: report.url,
      }),
    });
  } catch {
    // Silently fail — don't let error reporting cause more errors
  }

  // Also log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.group('🚨 Error Boundary Caught');
    console.error('Message:', report.message);
    console.error('Stack:', report.stack);
    console.error('Component Stack:', report.componentStack);
    console.groupEnd();
  }
}

// ─── Error Boundary Class Component ────────────────────────────────────────

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode | ((props: { error: Error; reset: () => void }) => ReactNode);
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'global' | 'section' | 'component';
  name?: string; // For identifying which boundary caught the error
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorId: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
      errorId: `err_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Report to backend
    reportError({
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack || undefined,
      url: typeof window !== 'undefined' ? window.location.href : '',
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null, errorId: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Custom fallback
      if (this.props.fallback) {
        if (typeof this.props.fallback === 'function') {
          return this.props.fallback({
            error: this.state.error,
            reset: this.reset,
          });
        }
        return this.props.fallback;
      }

      // Default fallback based on level
      const level = this.props.level || 'component';
      
      if (level === 'global') {
        return (
          <GlobalErrorFallback
            error={this.state.error}
            errorId={this.state.errorId!}
            reset={this.reset}
          />
        );
      }

      if (level === 'section') {
        return (
          <SectionErrorFallback
            error={this.state.error}
            name={this.props.name}
            reset={this.reset}
          />
        );
      }

      return (
        <ComponentErrorFallback
          error={this.state.error}
          reset={this.reset}
        />
      );
    }

    return this.props.children;
  }
}

// ─── Fallback UIs ──────────────────────────────────────────────────────────

function GlobalErrorFallback({
  error,
  errorId,
  reset,
}: {
  error: Error;
  errorId: string;
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full text-center"
      >
        <div className="text-6xl mb-4" role="img" aria-label="Error">
          ⚠️
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">
          Something went wrong
        </h1>
        <p className="text-gray-400 mb-6">
          An unexpected error occurred. Our team has been notified.
        </p>
        
        {process.env.NODE_ENV === 'development' && (
          <details className="mb-6 text-left bg-dark-surface rounded-lg p-4">
            <summary className="cursor-pointer text-sm text-gray-300 font-mono">
              Error Details (dev only)
            </summary>
            <pre className="mt-2 text-xs text-red-400 overflow-auto max-h-48 font-mono">
              {error.message}
              {'\n\n'}
              {error.stack}
            </pre>
          </details>
        )}

        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-bg"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="px-6 py-2.5 bg-dark-surface hover:bg-dark-border text-gray-300 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-dark-bg"
          >
            Go Home
          </button>
        </div>

        <p className="mt-4 text-xs text-gray-500 font-mono">
          Error ID: {errorId}
        </p>
      </motion.div>
    </div>
  );
}

function SectionErrorFallback({
  error,
  name,
  reset,
}: {
  error: Error;
  name?: string;
  reset: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full py-12 px-6"
      role="alert"
      aria-live="assertive"
    >
      <div className="max-w-sm mx-auto text-center bg-dark-surface/50 rounded-xl p-6 border border-dark-border">
        <div className="text-3xl mb-3" role="img" aria-label="Warning">
          ⚡
        </div>
        <h2 className="text-lg font-semibold text-white mb-1">
          {name ? `${name} failed to load` : 'Section failed to load'}
        </h2>
        <p className="text-sm text-gray-400 mb-4">
          This section encountered an error. The rest of the page is fine.
        </p>
        
        {process.env.NODE_ENV === 'development' && (
          <p className="text-xs text-red-400 font-mono mb-4 truncate">
            {error.message}
          </p>
        )}

        <button
          onClick={reset}
          className="px-4 py-2 text-sm bg-primary-600/20 hover:bg-primary-600/30 text-primary-400 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          Retry
        </button>
      </div>
    </motion.div>
  );
}

function ComponentErrorFallback({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-md"
      role="alert"
    >
      <span className="text-sm text-red-400">Failed to render</span>
      <button
        onClick={reset}
        className="text-xs text-red-300 hover:text-red-200 underline focus:outline-none"
      >
        retry
      </button>
    </div>
  );
}

// ─── Hook-based Error Boundary ─────────────────────────────────────────────

/**
 * useErrorHandler — imperatively trigger the nearest error boundary.
 * 
 * Useful for handling errors in event handlers or async operations
 * that aren't caught by React's error boundary mechanism.
 * 
 * Usage:
 *   const handleError = useErrorHandler();
 *   
 *   async function handleSubmit() {
 *     try {
 *       await api.createProject(data);
 *     } catch (error) {
 *       handleError(error);
 *     }
 *   }
 */
export function useErrorHandler(): (error: unknown) => void {
  const [, setState] = useState();

  return useCallback((error: unknown) => {
    setState(() => {
      if (error instanceof Error) throw error;
      throw new Error(String(error));
    });
  }, []);
}

// ─── Convenience Wrappers ──────────────────────────────────────────────────

/**
 * Wrap a page/section with an error boundary.
 * Simpler than using the class component directly.
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options?: {
    level?: 'global' | 'section' | 'component';
    name?: string;
    fallback?: ErrorBoundaryProps['fallback'];
  }
) {
  const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';
  
  function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary
        level={options?.level || 'section'}
        name={options?.name || displayName}
        fallback={options?.fallback}
      >
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  }
  
  WithErrorBoundary.displayName = `withErrorBoundary(${displayName})`;
  return WithErrorBoundary;
}
