import React, { Component, ErrorInfo, ReactNode } from 'react';
import AppFull from './AppFull';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>Something went wrong!</h1>
          <p style={{ color: 'red' }}>
            {this.state.error?.message || 'Unknown error occurred'}
          </p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <AppFull />
    </ErrorBoundary>
  );
}

export default AppWithErrorBoundary;