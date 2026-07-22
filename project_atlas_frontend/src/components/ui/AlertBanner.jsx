import { clsx } from 'clsx'
import { AlertTriangle, CheckCircle2, Info, XCircle, X } from 'lucide-react'
import { useState } from 'react'

const CONFIGS = {
  info:   { Icon:Info,          bg:'bg-blue-900/30',   border:'border-blue-700',   text:'text-blue-300'  },
  success:{ Icon:CheckCircle2,  bg:'bg-green-900/30',  border:'border-green-700',  text:'text-green-300' },
  warning:{ Icon:AlertTriangle, bg:'bg-yellow-900/30', border:'border-yellow-700', text:'text-yellow-300'},
  error:  { Icon:XCircle,       bg:'bg-red-900/30',    border:'border-red-700',    text:'text-red-300'   },
}

export function AlertBanner({ variant='info', title, children, dismissible=false, className='' }) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null
  const { Icon, bg, border, text } = CONFIGS[variant]||CONFIGS.info
  return (
    <div className={clsx('flex gap-3 p-4 rounded-xl border', bg, border, className)}>
      <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', text)} />
      <div className="flex-1 min-w-0">
        {title && <p className={clsx('text-sm font-semibold', text)}>{title}</p>}
        {children && <div className={clsx('text-sm mt-0.5 opacity-90', text)}>{children}</div>}
      </div>
      {dismissible && <button onClick={()=>setDismissed(true)} className={clsx('flex-shrink-0 opacity-60 hover:opacity-100', text)}><X className="w-4 h-4" /></button>}
    </div>
  )
}
