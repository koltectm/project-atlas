export const APP_NAME    = import.meta.env.VITE_APP_NAME    || 'Project Atlas'
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0'

export const API_BASE_URL  = import.meta.env.VITE_API_BASE_URL  || 'http://localhost:8000'
export const SUPABASE_URL  = import.meta.env.VITE_SUPABASE_URL  || ''
export const SUPABASE_ANON = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const SIMULATION_POLL_INTERVAL_MS = 2_000
export const RESULTS_REDIRECT_DELAY_MS   = 1_500
export const MAX_ITERATIONS              = 100_000

export const ITERATION_PRESETS = [
  { label: '1,000  (~quick preview)',          value: 1_000 },
  { label: '5,000  (~reliable)',               value: 5_000 },
  { label: '10,000 (~publication quality)',    value: 10_000 },
  { label: '50,000 (~high precision)',         value: 50_000 },
]

export const GEO_ZONES = {
  SS: { label: 'South-South (Niger Delta)', color: '#14b8a6' },
  SE: { label: 'South-East',                color: '#6366f1' },
  SW: { label: 'South-West (Lagos)',        color: '#3b82f6' },
  NC: { label: 'North-Central',             color: '#8b5cf6' },
  NW: { label: 'North-West',                color: '#f59e0b' },
  NE: { label: 'North-East',                color: '#ef4444' },
}

export const NODE_TYPES = {
  wellhead:         { label: 'Wellhead / Oil Field', color: '#f59e0b', stage: 'upstream' },
  pipeline:         { label: 'Pipeline',              color: '#3b82f6', stage: 'midstream' },
  export_terminal:  { label: 'Export Terminal',       color: '#14b8a6', stage: 'midstream' },
  refinery:         { label: 'Refinery',              color: '#a855f7', stage: 'midstream' },
  storage_depot:    { label: 'Storage Depot',         color: '#64748b', stage: 'midstream' },
  port:             { label: 'Port',                  color: '#06b6d4', stage: 'downstream' },
  distribution_hub: { label: 'Distribution Hub',      color: '#6366f1', stage: 'downstream' },
  consumer:         { label: 'Consumer',              color: '#9ca3af', stage: 'downstream' },
}

export const LINK_TYPES = {
  pipeline:  { label: 'Pipeline',  color: '#3b82f6', strokeDasharray: 'none' },
  road:      { label: 'Road',      color: '#9ca3af', strokeDasharray: '6 3' },
  sea_route: { label: 'Sea Route', color: '#06b6d4', strokeDasharray: '2 4' },
  rail:      { label: 'Rail',      color: '#4b5563', strokeDasharray: 'none' },
  river:     { label: 'River',     color: '#60a5fa', strokeDasharray: '8 2' },
}

export const DISRUPTION_CATEGORIES = {
  infrastructure: { label: 'Infrastructure', color: '#ef4444', icon: 'Wrench' },
  logistics:      { label: 'Logistics',       color: '#f97316', icon: 'Truck' },
  geopolitical:   { label: 'Geopolitical',    color: '#eab308', icon: 'Shield' },
  environmental:  { label: 'Environmental',   color: '#22c55e', icon: 'Cloud' },
  operational:    { label: 'Operational',     color: '#3b82f6', icon: 'Settings' },
  economic:       { label: 'Economic',        color: '#8b5cf6', icon: 'TrendingDown' },
  cybersecurity:  { label: 'Cybersecurity',   color: '#06b6d4', icon: 'Lock' },
  force_majeure:  { label: 'Force Majeure',   color: '#6b7280', icon: 'AlertTriangle' },
}

export const RISK_LEVELS = {
  critical: { min: 0.75, label: 'Critical', color: '#dc2626', bg: 'bg-red-600/20',    border: 'border-red-600' },
  high:     { min: 0.50, label: 'High',     color: '#ea580c', bg: 'bg-orange-600/20', border: 'border-orange-600' },
  medium:   { min: 0.25, label: 'Medium',   color: '#ca8a04', bg: 'bg-yellow-600/20', border: 'border-yellow-600' },
  low:      { min: 0.00, label: 'Low',      color: '#16a34a', bg: 'bg-green-600/20',  border: 'border-green-600' },
}

export function getRiskLevel(score) {
  if (score >= 0.75) return RISK_LEVELS.critical
  if (score >= 0.50) return RISK_LEVELS.high
  if (score >= 0.25) return RISK_LEVELS.medium
  return RISK_LEVELS.low
}
