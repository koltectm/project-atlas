import { format, formatDistanceToNow, parseISO } from 'date-fns'

export function formatUSD(value, decimals=2) {
  if (value==null||isNaN(value)) return '—'
  const abs=Math.abs(value)
  if (abs>=1e9) return `$${(value/1e9).toFixed(decimals)}B`
  if (abs>=1e6) return `$${(value/1e6).toFixed(decimals)}M`
  if (abs>=1e3) return `$${(value/1e3).toFixed(1)}K`
  return `$${value.toFixed(2)}`
}
export function formatUSDAxis(value) {
  if (value==null) return ''
  const abs=Math.abs(value)
  if (abs>=1e9) return `${(value/1e9).toFixed(1)}B`
  if (abs>=1e6) return `${(value/1e6).toFixed(0)}M`
  if (abs>=1e3) return `${(value/1e3).toFixed(0)}K`
  return value.toFixed(0)
}
export function formatPct(value, decimals=1) {
  if (value==null||isNaN(value)) return '—'
  return `${(value*100).toFixed(decimals)}%`
}
export function formatBarrels(value) {
  if (value==null) return '—'
  if (value>=1e6) return `${(value/1e6).toFixed(2)}M bbl`
  if (value>=1e3) return `${(value/1e3).toFixed(1)}K bbl`
  return `${value.toFixed(0)} bbl`
}
export function formatBpd(value) {
  if (value==null) return '—'
  if (value>=1e6) return `${(value/1e6).toFixed(2)}M bpd`
  if (value>=1e3) return `${(value/1e3).toFixed(0)}K bpd`
  return `${value.toFixed(0)} bpd`
}
export function formatNumber(value, decimals=0) {
  if (value==null||isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US',{minimumFractionDigits:decimals,maximumFractionDigits:decimals}).format(value)
}
export function formatIterations(value) {
  if (value==null) return '—'
  return new Intl.NumberFormat('en-US').format(value)
}
export function formatDate(dateStr) {
  if (!dateStr) return '—'
  try { return format(parseISO(dateStr),'dd MMM yyyy') } catch { return dateStr }
}
export function formatDateTime(dateStr) {
  if (!dateStr) return '—'
  try { return format(parseISO(dateStr),'dd MMM yyyy, HH:mm') } catch { return dateStr }
}
export function formatRelative(dateStr) {
  if (!dateStr) return '—'
  try { return formatDistanceToNow(parseISO(dateStr),{addSuffix:true}) } catch { return dateStr }
}
export function formatDays(days, decimals=1) {
  if (days==null||isNaN(days)) return '—'
  if (days===0) return '0 days'
  if (days<1) return `${(days*24).toFixed(1)} hours`
  return `${days.toFixed(decimals)} days`
}
export function formatSeconds(seconds) {
  if (seconds==null) return '—'
  if (seconds<1) return `${(seconds*1000).toFixed(0)}ms`
  if (seconds<60) return `${seconds.toFixed(1)}s`
  return `${Math.floor(seconds/60)}m ${Math.round(seconds%60)}s`
}
export function formatScore(value, decimals=3) {
  if (value==null||isNaN(value)) return '—'
  return value.toFixed(decimals)
}
export function formatProbability(value) {
  if (value==null||isNaN(value)) return '—'
  const pct=value*100
  if (pct<1) return '<1%'
  return `${pct.toFixed(1)}%`
}
