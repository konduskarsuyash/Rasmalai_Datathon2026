import React from 'react';

/**
 * ErrorBoundary — catches rendering errors and shows a fallback UI
 * instead of a white screen. This is critical for simulation because
 * rapid state updates from SSE events can occasionally trigger rendering
 * errors in child components.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Caught rendering error:', error);
    console.error('[ErrorBoundary] Component stack:', errorInfo?.componentStack);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-8">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-lg w-full space-y-4">
            <h2 className="text-2xl font-bold text-red-600 flex items-center gap-2">
              <span>⚠️</span>
              <span>Something went wrong</span>
            </h2>
            <p className="text-gray-600">
              A rendering error occurred during the simulation. This is usually
              caused by unexpected data from the backend.
            </p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 max-h-40 overflow-y-auto">
              <strong>Error:</strong> {this.state.error?.message || 'Unknown error'}
            </div>
            {this.state.errorInfo?.componentStack && (
              <details className="text-xs text-gray-500">
                <summary className="cursor-pointer font-semibold">Component Stack</summary>
                <pre className="mt-2 whitespace-pre-wrap overflow-auto max-h-40">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            <div className="flex gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-semibold transition-colors"
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

export default ErrorBoundary;
