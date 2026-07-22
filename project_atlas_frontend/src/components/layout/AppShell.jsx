import { Outlet } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Sidebar } from './Sidebar.jsx'
import { TopBar } from './TopBar.jsx'
import useUiStore from '@/store/uiStore.js'
import { clsx } from 'clsx'

export function AppShell() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed)
  return (
    <div className="flex h-screen bg-surface-900 overflow-hidden">
      <Sidebar />
      <div className={clsx('flex flex-col flex-1 min-w-0 transition-all duration-300', collapsed?'ml-16':'ml-64')}>
        <TopBar />
        <main className="flex-1 overflow-y-auto"><div className="p-6"><Outlet /></div></main>
      </div>
      <Toaster position="top-right" toastOptions={{ style:{ background:'#162035', border:'1px solid #263650', color:'#e5e7eb', fontSize:'14px' }, success:{iconTheme:{primary:'#16a34a',secondary:'#162035'}}, error:{iconTheme:{primary:'#dc2626',secondary:'#162035'}} }} />
    </div>
  )
}
