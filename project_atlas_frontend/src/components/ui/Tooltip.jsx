import { useState } from 'react'
import { clsx } from 'clsx'

export function Tooltip({ children, content, placement='top', className='' }) {
  const [visible, setVisible] = useState(false)
  const placements = { top:'bottom-full left-1/2 -translate-x-1/2 mb-2', bottom:'top-full left-1/2 -translate-x-1/2 mt-2', left:'right-full top-1/2 -translate-y-1/2 mr-2', right:'left-full top-1/2 -translate-y-1/2 ml-2' }
  if (!content) return children
  return (
    <div className={clsx('relative inline-flex', className)} onMouseEnter={()=>setVisible(true)} onMouseLeave={()=>setVisible(false)} onFocus={()=>setVisible(true)} onBlur={()=>setVisible(false)}>
      {children}
      {visible && <div className={clsx('absolute z-50 px-2.5 py-1.5 text-xs text-white bg-surface-600 border border-surface-400 rounded-lg shadow-xl whitespace-nowrap pointer-events-none', placements[placement]||placements.top)}>{content}</div>}
    </div>
  )
}
