import { clsx } from 'clsx'

export function PageHeader({ title, description, actions, breadcrumb, className='' }) {
  return (
    <div className={clsx('flex items-start justify-between mb-6', className)}>
      <div>
        {breadcrumb && <p className="text-xs text-gray-500 mb-1">{breadcrumb}</p>}
        <h2 className="text-xl font-bold text-white">{title}</h2>
        {description && <p className="text-sm text-gray-400 mt-1 max-w-2xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-3 ml-4 flex-shrink-0">{actions}</div>}
    </div>
  )
}
