"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex flex-col items-center justify-center p-12 bg-[#0a0a0f] border border-red-900/30 rounded-xl my-4">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Something went wrong</h2>
          <p className="text-slate-400 text-sm mb-4 text-center max-w-md">
            The platform encountered an unexpected error while rendering this component.
          </p>
          <div className="bg-black/50 p-4 rounded text-xs text-red-400 font-mono w-full overflow-auto max-h-32">
            {this.state.error?.message || "Unknown error"}
          </div>
          <button
            className="mt-6 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded transition-colors text-sm"
            onClick={() => this.setState({ hasError: false })}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
