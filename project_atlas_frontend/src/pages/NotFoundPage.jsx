import { Link } from 'react-router-dom'
import { ShieldAlert, Home } from 'lucide-react'
import { Button } from '@/components/ui/Button.jsx'

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-surface-900 flex flex-col items-center justify-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-surface-700 border border-surface-500
                      flex items-center justify-center mb-6">
        <ShieldAlert className="w-8 h-8 text-gray-500" />
      </div>
      <h1 className="text-5xl font-bold text-white font-mono">404</h1>
      <p className="text-gray-400 mt-2 mb-6">Page not found</p>
      <Link to="/dashboard">
        <Button variant="primary" icon={Home}>Back to Dashboard</Button>
      </Link>
    </div>
  )
}
