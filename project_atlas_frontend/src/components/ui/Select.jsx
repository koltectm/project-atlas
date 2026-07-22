import { forwardRef } from 'react'
import { clsx } from 'clsx'
import { ChevronDown } from 'lucide-react'

export const Select = forwardRef(function Select({ label, error, hint, options=[], className='', placeholder, ...props }, ref) {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-gray-300">{label}{props.required&&<span className="ml-1 text-red-400">*</span>}</label>}
      <div className="relative">
        <select ref={ref} className={clsx('w-full appearance-none rounded-lg border bg-surface-700 text-gray-100 text-sm px-3 py-2.5 pr-9 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 disabled:opacity-50 disabled:cursor-not-allowed', error?'border-red-500':'border-surface-500', className)} {...props}>
          {placeholder && <option value="" disabled>{placeholder}</option>}
          {options.map((opt) => <option key={opt.value} value={opt.value} className="bg-surface-800">{opt.label}</option>)}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  )
})
