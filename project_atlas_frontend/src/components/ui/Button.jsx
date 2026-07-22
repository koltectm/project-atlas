import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

const VARIANTS = {
  primary:  'bg-primary-600 hover:bg-primary-500 text-white border border-primary-500',
  secondary:'bg-surface-700 hover:bg-surface-600 text-gray-200 border border-surface-500',
  danger:   'bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-600/50',
  ghost:    'bg-transparent hover:bg-surface-700 text-gray-300',
  success:  'bg-accent-500 hover:bg-accent-600 text-white border border-accent-500',
  outline:  'bg-transparent border border-primary-500 text-primary-400 hover:bg-primary-500/10',
  warning:  'bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/50',
}
const SIZES = { xs:'h-7 px-2.5 text-xs gap-1.5', sm:'h-8 px-3 text-sm gap-1.5', md:'h-10 px-4 text-sm gap-2', lg:'h-12 px-6 text-base gap-2' }

export function Button({ children, variant='primary', size='md', loading=false, disabled=false, className='', icon:Icon, iconRight:IconRight, ...props }) {
  return (
    <button
      disabled={disabled||loading}
      className={clsx('inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50 disabled:opacity-50 disabled:cursor-not-allowed', VARIANTS[variant], SIZES[size], className)}
      {...props}
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : Icon && <Icon className="w-4 h-4 flex-shrink-0" />}
      {children}
      {!loading && IconRight && <IconRight className="w-4 h-4 flex-shrink-0" />}
    </button>
  )
}
