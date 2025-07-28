import React, { Component, ErrorInfo, ReactNode } from 'react';
import App from './App';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  };

  public static getDerivedStateFromError(error: Error): State {
    console.error('Error caught by boundary:', error);
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error details:', {
      error: error.toString(),
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorBoundary: errorInfo.errorBoundary
    });
    
    this.setState({
      error,
      errorInfo
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-red-600 mb-2">
                Something went wrong
              </h1>
              <p className="text-gray-600">
                An unexpected error occurred. The error details have been logged to the console.
              </p>
            </div>
            
            {this.state.error && (
              <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">Error Message:</h2>
                <pre className="bg-red-50 p-4 rounded border border-red-200 text-sm overflow-x-auto">
                  {this.state.error.toString()}
                </pre>
              </div>
            )}
            
            {process.env.NODE_ENV === 'development' && this.state.error?.stack && (
              <details className="mb-6">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                  Show stack trace
                </summary>
                <pre className="mt-2 bg-gray-100 p-4 rounded text-xs overflow-x-auto">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            
            {process.env.NODE_ENV === 'development' && this.state.errorInfo?.componentStack && (
              <details className="mb-6">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                  Show component stack
                </summary>
                <pre className="mt-2 bg-gray-100 p-4 rounded text-xs overflow-x-auto">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            
            <div className="flex gap-4">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}

export default AppWithErrorBoundary;