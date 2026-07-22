import { NavLink, useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'
import { LayoutDashboard, Network, FlaskConical, Play, BarChart3, GitCompare, Settings, LogOut, ChevronLeft, Activity, ShieldAlert } from 'lucide-react'
import useUiStore from '@/store/uiStore.js'
import useAuthStore from '@/store/authStore.js'
import { Tooltip } from '@/components/ui/Tooltip.jsx'
import { APP_NAME } from '@/config/constants.js'

const NAV = [
  {to:'/dashboard',label:'Dashboard',Icon:LayoutDashboard},
  {to:'/network',label:'Supply Chain Map',Icon:Network},
  {to:'/scenarios',label:'Scenarios',Icon:FlaskConical},
  {to:'/simulation',label:'Simulation',Icon:Play},
  {to:'/results',label:'Results',Icon:BarChart3},
  {to:'/analytics',label:'Analytics',Icon:Activity},
  {to:'/compare',label:'Compare Runs',Icon:GitCompare},
]

export function Sidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed)
  const toggle    = useUiStore((s) => s.toggleSidebar)
  const logout    = useAuthStore((s) => s.logout)
  const profile   = useAuthStore((s) => s.profile)
  const navigate  = useNavigate()

  const handleLogout = async () => { await logout(); navigate('/auth') }

  return (
    <aside className={clsx('fixed inset-y-0 left-0 z-40 flex flex-col bg-surface-800 border-r border-surface-500 transition-all duration-300', collapsed?'w-16':'w-64')}>
      <div className={clsx('flex items-center h-16 border-b border-surface-500 px-4 flex-shrink-0', collapsed?'justify-center':'justify-between')}>
        {!collapsed && <div className="flex items-center gap-2.5 overflow-hidden"><div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center flex-shrink-0"><ShieldAlert className="w-4 h-4 text-white"/></div><span className="text-sm font-bold text-white truncate">{APP_NAME}</span></div>}
        {collapsed && <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center"><ShieldAlert className="w-4 h-4 text-white"/></div>}
        {!collapsed && <button onClick={toggle} className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-white hover:bg-surface-600 transition-colors"><ChevronLeft className="w-4 h-4"/></button>}
      </div>
      {collapsed && <button onClick={toggle} className="flex items-center justify-center h-10 mx-2 mt-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-600 transition-colors"><ChevronLeft className="w-4 h-4 rotate-180"/></button>}
      <nav className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
        {NAV.map(({to,label,Icon})=>(
          <Tooltip key={to} content={collapsed?label:null} placement="right">
            <NavLink to={to} className={({isActive})=>clsx('flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150', collapsed?'justify-center':'', isActive?'bg-primary-600/20 text-primary-300 border border-primary-600/40':'text-gray-400 hover:text-gray-200 hover:bg-surface-700')}>
              <Icon className="w-5 h-5 flex-shrink-0"/>
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          </Tooltip>
        ))}
      </nav>
      <div className="border-t border-surface-500 py-3 px-2 space-y-1 flex-shrink-0">
        {!collapsed && profile && <div className="px-3 py-2"><p className="text-xs font-medium text-gray-300 truncate">{profile.full_name}</p><p className="text-2xs text-gray-500 capitalize">{profile.role}</p></div>}
        <Tooltip content={collapsed?'Log out':null} placement="right">
          <button onClick={handleLogout} className={clsx('w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-400 hover:text-red-400 hover:bg-red-900/20 transition-all duration-150', collapsed?'justify-center':'')}>
            <LogOut className="w-5 h-5 flex-shrink-0"/>
            {!collapsed && <span>Log out</span>}
          </button>
        </Tooltip>
      </div>
    </aside>
  )
}
