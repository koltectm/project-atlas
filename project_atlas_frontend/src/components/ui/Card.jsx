import { clsx } from 'clsx'

export function Card({ children, className='', hover=false, ...props }) {
  return (
    <div className={clsx('rounded-xl border border-surface-500 bg-surface-800 shadow-card transition-all duration-200', hover&&'hover:border-surface-400 hover:shadow-card-hover cursor-pointer', className)} {...props}>
      {children}
    </div>
  )
}
export function CardHeader({ children, className='', action }) {
  return (
    <div className={clsx('flex items-center justify-between px-5 py-4 border-b border-surface-500', className)}>
      <div className="flex-1">{children}</div>
      {action && <div className="ml-4 flex-shrink-0">{action}</div>}
    </div>
  )
}
export function CardBody({ children, className='' }) {
  return <div className={clsx('px-5 py-4', className)}>{children}</div>
}
export function CardTitle({ children, className='' }) {
  return <h3 className={clsx('text-base font-semibold text-white', className)}>{children}</h3>
}
export function CardDescription({ children, className='' }) {
  return <p className={clsx('text-sm text-gray-400 mt-0.5', className)}>{children}</p>
}
