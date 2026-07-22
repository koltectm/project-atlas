import { clsx } from 'clsx'

const VARIANTS = {
  default:'bg-surface-600 text-gray-300 border-surface-500', primary:'bg-primary-900/50 text-primary-300 border-primary-700',
  success:'bg-green-900/30 text-green-400 border-green-700', warning:'bg-yellow-900/30 text-yellow-400 border-yellow-700',
  danger:'bg-red-900/30 text-red-400 border-red-700', info:'bg-blue-900/30 text-blue-400 border-blue-700',
  queued:'bg-gray-800 text-gray-400 border-gray-600', running:'bg-blue-900/40 text-blue-300 border-blue-600 animate-pulse-slow',
  completed:'bg-green-900/30 text-green-400 border-green-700', failed:'bg-red-900/30 text-red-400 border-red-700',
  draft:'bg-surface-600 text-gray-400 border-surface-500',
}

export function Badge({ children, variant='default', dot=false, className='' }) {
  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full border', VARIANTS[variant]||VARIANTS.default, className)}>
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0', variant==='running'&&'bg-blue-400', variant==='completed'&&'bg-green-400', variant==='failed'&&'bg-red-400', ['draft','queued'].includes(variant)&&'bg-gray-500')} />}
      {children}
    </span>
  )
}

export function StatusBadge({ status }) {
  const map = { queued:{label:'Queued',variant:'queued'}, running:{label:'Running',variant:'running'}, completed:{label:'Completed',variant:'completed'}, failed:{label:'Failed',variant:'failed'}, draft:{label:'Draft',variant:'draft'} }
  const { label, variant } = map[status]||{ label:status, variant:'default' }
  return <Badge variant={variant} dot>{label}</Badge>
}
