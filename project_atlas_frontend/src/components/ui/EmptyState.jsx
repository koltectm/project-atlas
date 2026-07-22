import { clsx } from 'clsx'

export function EmptyState({ icon:Icon, title, description, action, className='' }) {
  return (
    <div className={clsx('flex flex-col items-center justify-center py-16 px-6 text-center', className)}>
      {Icon && <div className="w-16 h-16 rounded-2xl bg-surface-700 border border-surface-500 flex items-center justify-center mb-4"><Icon className="w-8 h-8 text-gray-500" /></div>}
      <h3 className="text-base font-semibold text-gray-300 mb-2">{title}</h3>
      {description && <p className="text-sm text-gray-500 max-w-sm mb-6">{description}</p>}
      {action}
    </div>
  )
}
