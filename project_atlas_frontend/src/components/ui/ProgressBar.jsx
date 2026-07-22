import { clsx } from 'clsx'

export function ProgressBar({ value=0, max=100, label, showPct=true, color='primary', className='' }) {
  const pct=Math.min(100,Math.max(0,(value/max)*100))
  const colors = { primary:'bg-primary-500', success:'bg-green-500', warning:'bg-yellow-500', danger:'bg-red-500', accent:'bg-accent-500' }
  return (
    <div className={clsx('space-y-1.5', className)}>
      {(label||showPct) && <div className="flex justify-between items-center text-xs text-gray-400">{label&&<span>{label}</span>}{showPct&&<span className="font-mono tabular-nums">{pct.toFixed(1)}%</span>}</div>}
      <div className="h-2 bg-surface-600 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all duration-500', colors[color])} style={{width:`${pct}%`}} />
      </div>
    </div>
  )
}

export function CircularProgress({ value=0, size=200, strokeWidth=8, className='' }) {
  const radius=(size-strokeWidth)/2, circumference=2*Math.PI*radius
  const pct=Math.min(100,Math.max(0,value)), offset=circumference-(pct/100)*circumference
  return (
    <div className={clsx('relative inline-flex items-center justify-center', className)} style={{width:size,height:size}}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#1e2d45" strokeWidth={strokeWidth} />
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#2563eb" strokeWidth={strokeWidth} strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} className="transition-all duration-500" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-mono font-bold text-white tabular-nums">{Math.round(pct)}%</span>
      </div>
    </div>
  )
}
