/**
 * src/pages/AuthPage.jsx
 * ========================
 * Login/Register tab toggle page.
 */
import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import { clsx } from 'clsx'
import { LoginForm }    from '@/components/auth/LoginForm.jsx'
import { RegisterForm } from '@/components/auth/RegisterForm.jsx'
import useAuthStore from '@/store/authStore.js'
import { APP_NAME } from '@/config/constants.js'

export function AuthPage() {
  const [tab, setTab]   = useState('login')
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-surface-900 bg-grid flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-white">{APP_NAME}</span>
        </Link>

        <div className="bg-surface-800 border border-surface-500 rounded-2xl shadow-card p-8">
          {/* Tab toggle */}
          <div className="flex rounded-lg border border-surface-500 overflow-hidden mb-6">
            {[
              { key: 'login',    label: 'Sign In' },
              { key: 'register', label: 'Create Account' },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={clsx(
                  'flex-1 py-2.5 text-sm font-medium transition-all duration-150',
                  tab === key
                    ? 'bg-primary-600/20 text-primary-300'
                    : 'bg-surface-700 text-gray-400 hover:text-gray-200'
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {tab === 'login' ? <LoginForm /> : <RegisterForm />}
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Nigerian Oil & Gas Supply Chain Stress-Testing System
        </p>
      </div>
    </div>
  )
}
