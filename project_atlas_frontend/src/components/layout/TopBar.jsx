import { Bell } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import useAuthStore from '@/store/authStore.js'
import useSimulationStore from '@/store/simulationStore.js'
import { Badge } from '@/components/ui/Badge.jsx'

const PAGE_TITLES = {
  '/dashboard':'Dashboard','/network':'Supply Chain Map','/scenarios':'Scenarios',
  '/simulation':'Simulation Runner','/results':'Results','/analytics':'Analytics & OR Engine',
  '/compare':'Run Comparison','/settings':'Settings',
}

export function TopBar() {
  const location    = useLocation()
  const profile     = useAuthStore((s) => s.profile)
  const runStatus   = useSimulationStore((s) => s.activeRunStatus)
  const progressPct = useSimulationStore((s) => s.progressPct)

  const title = Object.entries(PAGE_TITLES).filter(([path]) => location.pathname.startsWith(path))
    .sort((a,b) => b[0].length-a[0].length)[0]?.[1] || 'Project Atlas'

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-surface-500 bg-surface-800 flex-shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-sm font-semibold text-white">{title}</h1>
        {runStatus==='running' && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-xs text-blue-300 font-mono tabular-nums">{progressPct}% complete</span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-3">
        {profile?.role && <Badge variant={profile.role==='admin'?'danger':profile.role==='analyst'?'primary':'default'}>{profile.role}</Badge>}
        <button className="w-9 h-9 flex items-center justify-center rounded-lg text-gray-400 hover:text-white hover:bg-surface-600 transition-colors"><Bell className="w-4 h-4" /></button>
        <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-xs font-bold text-white">
          {profile?.full_name?.[0]?.toUpperCase()||'?'}
        </div>
      </div>
    </header>
  )
}
