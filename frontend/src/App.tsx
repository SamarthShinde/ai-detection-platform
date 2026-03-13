import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastProvider } from './components/Toast'
import ProtectedRoute from './components/ProtectedRoute'
import { PageLoader } from './components/LoadingStates'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const AuthPage = lazy(() => import('./pages/AuthPage'))
const VerificationPage = lazy(() => import('./pages/VerificationPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const UploadPage = lazy(() => import('./pages/UploadPage'))
const ResultsPage = lazy(() => import('./pages/ResultsPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const BatchPage = lazy(() => import('./pages/BatchPage'))
const APIKeysPage = lazy(() => import('./pages/APIKeysPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))

class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen bg-slate-900 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-white mb-2">Something went wrong</h2>
              <p className="text-slate-400 mb-4">{this.state.error?.message}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Reload Page
              </button>
            </div>
          </div>
        )
      )
    }
    return this.props.children
  }
}

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route
              path="/"
              element={
                <ErrorBoundary>
                  <LandingPage />
                </ErrorBoundary>
              }
            />
            <Route
              path="/auth"
              element={
                <ErrorBoundary>
                  <AuthPage />
                </ErrorBoundary>
              }
            />
            <Route
              path="/verify"
              element={
                <ErrorBoundary>
                  <VerificationPage />
                </ErrorBoundary>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <DashboardPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <UploadPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/results/:id"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <ResultsPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <HistoryPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/batch"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <BatchPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/api-keys"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <APIKeysPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <SettingsPage />
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
