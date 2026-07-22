import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import { exportResultsPdf, exportResultsCsv, exportVulnerabilityCsv, exportElementAsPng } from '@/utils/exportHelpers.js'

export function useExport() {
  const [isExporting, setIsExporting] = useState(false)

  const withLoading = useCallback(async (fn, successMsg='Export complete') => {
    setIsExporting(true)
    try { await fn(); toast.success(successMsg) }
    catch (err) { console.error('Export failed:',err); toast.error('Export failed') }
    finally { setIsExporting(false) }
  }, [])

  const exportPdf               = useCallback((runId,aggregates,scenarioName) => withLoading(()=>exportResultsPdf(runId,aggregates,scenarioName),'PDF exported'), [withLoading])
  const exportCsv               = useCallback((aggregates,filename)            => withLoading(()=>exportResultsCsv(aggregates,filename),'CSV exported'), [withLoading])
  const exportVulnerabilityToCsv= useCallback((assessments,filename)            => withLoading(()=>exportVulnerabilityCsv(assessments,filename),'CSV exported'), [withLoading])
  const exportChartPng          = useCallback((elementId,filename)              => withLoading(()=>exportElementAsPng(elementId,filename),'PNG exported'), [withLoading])

  return { isExporting, exportPdf, exportCsv, exportVulnerabilityToCsv, exportChartPng }
}
