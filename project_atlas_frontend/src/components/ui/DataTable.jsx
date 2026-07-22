import { useState, useMemo } from 'react'
import { clsx } from 'clsx'
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { Spinner } from './Spinner.jsx'
import { EmptyState } from './EmptyState.jsx'
import { Button } from './Button.jsx'

export function DataTable({ columns=[], data=[], pageSize=25, loading=false, emptyTitle='No data', emptyDesc='', className='', rowKey='id', onRowClick }) {
  const [sortKey, setSortKey]= useState(null)
  const [sortDir, setSortDir]= useState('asc')
  const [page, setPage]      = useState(1)

  const handleSort=(key)=>{ if(sortKey===key) setSortDir((d)=>d==='asc'?'desc':'asc'); else{setSortKey(key);setSortDir('asc')} setPage(1) }

  const sorted=useMemo(()=>{
    if (!sortKey) return data
    return [...data].sort((a,b)=>{
      const va=a[sortKey],vb=b[sortKey]
      if(va==null&&vb==null) return 0; if(va==null) return 1; if(vb==null) return -1
      const cmp=typeof va==='string'?va.localeCompare(vb):va-vb
      return sortDir==='asc'?cmp:-cmp
    })
  },[data,sortKey,sortDir])

  const totalPages=Math.ceil(sorted.length/pageSize)
  const paged=sorted.slice((page-1)*pageSize,page*pageSize)

  const SortIcon=({col})=>{
    if(!col.sortable) return null
    if(sortKey!==col.key) return <ChevronsUpDown className="w-3.5 h-3.5 text-gray-600" />
    return sortDir==='asc'?<ChevronUp className="w-3.5 h-3.5 text-primary-400"/>:<ChevronDown className="w-3.5 h-3.5 text-primary-400"/>
  }

  return (
    <div className={clsx('flex flex-col', className)}>
      <div className="overflow-x-auto rounded-xl border border-surface-500">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-500 bg-surface-700">
              {columns.map((col)=>(
                <th key={col.key} className={clsx('px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider', col.sortable&&'cursor-pointer select-none hover:text-gray-200', col.align==='right'&&'text-right', col.align==='center'&&'text-center', col.width)} onClick={col.sortable?()=>handleSort(col.key):undefined}>
                  <div className={clsx('flex items-center gap-1.5', col.align==='right'&&'justify-end', col.align==='center'&&'justify-center')}>{col.label}<SortIcon col={col}/></div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading?(<tr><td colSpan={columns.length} className="py-16 text-center"><Spinner className="mx-auto"/></td></tr>)
            :paged.length===0?(<tr><td colSpan={columns.length}><EmptyState title={emptyTitle} description={emptyDesc}/></td></tr>)
            :paged.map((row,i)=>(
              <tr key={row[rowKey]||i} className={clsx('border-b border-surface-600 bg-surface-800 hover:bg-surface-700 transition-colors', onRowClick&&'cursor-pointer')} onClick={onRowClick?()=>onRowClick(row):undefined}>
                {columns.map((col)=>(
                  <td key={col.key} className={clsx('px-4 py-3 text-gray-200', col.align==='right'&&'text-right font-mono tabular-nums', col.align==='center'&&'text-center')}>
                    {col.render?col.render(row[col.key],row):(row[col.key]??'—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages>1&&(
        <div className="flex items-center justify-between mt-3 px-1">
          <p className="text-xs text-gray-500">Showing {(page-1)*pageSize+1}–{Math.min(page*pageSize,sorted.length)} of {sorted.length}</p>
          <div className="flex items-center gap-2">
            <Button size="xs" variant="secondary" onClick={()=>setPage((p)=>Math.max(1,p-1))} disabled={page===1} icon={ChevronLeft}/>
            <span className="text-xs text-gray-400 font-mono">{page}/{totalPages}</span>
            <Button size="xs" variant="secondary" onClick={()=>setPage((p)=>Math.min(totalPages,p+1))} disabled={page===totalPages} icon={ChevronRight}/>
          </div>
        </div>
      )}
    </div>
  )
}
