import { clsx } from 'clsx'

export function Spinner({ size='md', className='' }) {
  const sizes = { sm:'w-4 h-4', md:'w-6 h-6', lg:'w-10 h-10', xl:'w-16 h-16' }
  return <div className={clsx('border-2 border-surface-500 border-t-primary-500 rounded-full animate-spin', sizes[size], className)} />
}

export function PageSpinner({ message='Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface-900 gap-4">
      <Spinner size="xl" />
      <p className="text-gray-400 text-sm">{message}</p>
    </div>
  )
}
