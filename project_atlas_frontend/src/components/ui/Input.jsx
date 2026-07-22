import { forwardRef } from 'react'
import { clsx } from 'clsx'

export const Input = forwardRef(function Input({ label, error, hint, className='', icon:Icon, ...props }, ref) {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-gray-300">{label}{props.required&&<span className="ml-1 text-red-400">*</span>}</label>}
      <div className="relative">
        {Icon && <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none"><Icon className="w-4 h-4 text-gray-500" /></div>}
        <input ref={ref}
          className={clsx('w-full rounded-lg border bg-surface-700 text-gray-100 placeholder-gray-500 text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 disabled:opacity-50 disabled:cursor-not-allowed', Icon?'pl-9 pr-3 py-2.5':'px-3 py-2.5', error?'border-red-500':'border-surface-500', className)}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  )
})
