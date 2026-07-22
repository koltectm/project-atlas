import { useState } from 'react'
import { Plus, Search } from 'lucide-react'
import { clsx } from 'clsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { Input } from '@/components/ui/Input.jsx'
import { DISRUPTION_CATEGORIES } from '@/config/constants.js'
import { formatProbability } from '@/utils/formatters.js'
import { useDisruptionTypes } from '@/hooks/useScenario.js'

const CAT_KEYS = Object.keys(DISRUPTION_CATEGORIES)

export function DisruptionPicker({ selectedIds=new Set(), onAdd }) {
  const { disruptionTypes, isLoading } = useDisruptionTypes()
  const [activeCategory, setActiveCategory] = useState(CAT_KEYS[0])
  const [searchQuery,    setSearchQuery]     = useState('')

  const filtered = disruptionTypes.filter((d) => {
    const matchCat    = d.category === activeCategory
    const matchSearch = !searchQuery || d.name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchCat && matchSearch
  })

  if (isLoading) return <div className="flex justify-center py-12"><Spinner/></div>

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4"><Input placeholder="Search disruption types…" icon={Search} value={searchQuery} onChange={(e)=>setSearchQuery(e.target.value)}/></div>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {CAT_KEYS.map((cat)=>{ const info=DISRUPTION_CATEGORIES[cat], count=disruptionTypes.filter((d)=>d.category===cat).length; return (
          <button key={cat} onClick={()=>setActiveCategory(cat)}
            className={clsx('px-2.5 py-1 text-xs rounded-lg border transition-all duration-150 font-medium', activeCategory===cat?'text-white':'bg-surface-700 border-surface-500 text-gray-400 hover:text-gray-200')}
            style={activeCategory===cat?{backgroundColor:info.color+'30',borderColor:info.color+'80',color:info.color}:{}}>
            {info.label} ({count})
          </button>
        )})}
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {filtered.length===0 && <p className="text-xs text-gray-500 text-center py-8">No disruption types match.</p>}
        {filtered.map((d) => {
          const added = selectedIds.has(d.disruption_type_id)
          return (
            <div key={d.disruption_type_id} className="rounded-xl border border-surface-500 bg-surface-700 p-3 hover:border-surface-400 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{d.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{d.description}</p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className="text-2xs text-gray-500">p={formatProbability(d.typical_annual_probability)}/yr</span>
                    <span className="text-2xs text-gray-500">{d.typical_duration_days_min}–{d.typical_duration_days_max} days</span>
                  </div>
                </div>
                <Button size="xs" variant={added?'secondary':'primary'} onClick={()=>!added&&onAdd(d)} disabled={added} icon={Plus} className="flex-shrink-0">{added?'Added':'Add'}</Button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
