export async function exportElementAsPng(elementId, filename='chart.png') {
  const { default: html2canvas } = await import('html2canvas')
  const element = document.getElementById(elementId)
  if (!element) throw new Error(`Element #${elementId} not found`)
  const canvas = await html2canvas(element, { backgroundColor:'#0f1629', scale:2, useCORS:true, logging:false })
  const link = document.createElement('a')
  link.download = filename
  link.href = canvas.toDataURL('image/png')
  link.click()
}

export async function exportResultsPdf(runId, aggregates, scenarioName) {
  const { default: html2canvas } = await import('html2canvas')
  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF({ orientation:'portrait', unit:'mm', format:'a4' })
  const pageW = pdf.internal.pageSize.getWidth(), margin = 15

  pdf.setFillColor(10,15,30); pdf.rect(0,0,pageW,297,'F')
  pdf.setTextColor(59,130,246); pdf.setFontSize(24); pdf.setFont('helvetica','bold')
  pdf.text('PROJECT ATLAS', pageW/2, 60, { align:'center' })
  pdf.setTextColor(255,255,255); pdf.setFontSize(16); pdf.setFont('helvetica','normal')
  pdf.text('Monte Carlo Simulation Results', pageW/2, 75, { align:'center' })
  pdf.setFontSize(12); pdf.setTextColor(156,163,175)
  pdf.text(`Scenario: ${scenarioName||'Unknown'}`, pageW/2, 100, { align:'center' })
  pdf.text(`Run ID: ${runId}`, pageW/2, 110, { align:'center' })
  pdf.text(`Generated: ${new Date().toISOString()}`, pageW/2, 120, { align:'center' })

  pdf.addPage(); pdf.setFillColor(10,15,30); pdf.rect(0,0,pageW,297,'F')
  pdf.setTextColor(59,130,246); pdf.setFontSize(14); pdf.setFont('helvetica','bold')
  pdf.text('Statistical Summary', margin, 25)
  pdf.setTextColor(200,200,200); pdf.setFontSize(9); pdf.setFont('helvetica','normal')
  let y = 40
  ;(aggregates||[]).forEach((m) => {
    pdf.text(`${m.metric_name}`, margin, y)
    pdf.text(`Mean: ${m.mean_value?.toFixed(2)||'---'}`, margin+70, y)
    pdf.text(`VaR-95: ${m.var_95?.toFixed(2)||'---'}`, margin+120, y)
    pdf.text(`CVaR-95: ${m.cvar_95?.toFixed(2)||'---'}`, margin+160, y)
    y += 8
    if (y > 270) { pdf.addPage(); y = 25 }
  })

  for (const chartId of ['chart-cost-distribution','chart-flow-distribution','chart-vulnerability']) {
    const el = document.getElementById(chartId)
    if (!el) continue
    pdf.addPage(); pdf.setFillColor(10,15,30); pdf.rect(0,0,pageW,297,'F')
    const canvas = await html2canvas(el, { backgroundColor:'#0f1629', scale:2, useCORS:true, logging:false })
    const imgData = canvas.toDataURL('image/png')
    const imgW = pageW - 2*margin, imgH = (canvas.height/canvas.width)*imgW
    pdf.addImage(imgData, 'PNG', margin, 20, imgW, Math.min(imgH, 250))
  }

  pdf.save(`atlas-results-${runId}.pdf`)
}

export function exportResultsCsv(aggregates, filename='atlas-results.csv') {
  if (!aggregates?.length) return
  const headers = ['metric_name','mean_value','std_deviation','percentile_5','percentile_25',
    'median_value','percentile_75','percentile_95','min_value','max_value','var_95','cvar_95','skewness','kurtosis']
  const rows = aggregates.map((a) =>
    headers.map((h) => { const v=a[h]; return v==null?'':typeof v==='number'?v.toFixed(6):v }).join(',')
  )
  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a'); link.href=url; link.download=filename; link.click()
  URL.revokeObjectURL(url)
}

export function exportVulnerabilityCsv(assessments, filename='atlas-vulnerability.csv') {
  if (!assessments?.length) return
  const headers = ['criticality_rank','entity_type','entity_id','vulnerability_score',
    'failure_frequency','avg_impact_cost_usd','avg_impact_delay_days','bottleneck_score','betweenness_centrality']
  const rows = assessments.map((a) =>
    headers.map((h) => { const v=a[h]; return v==null?'':typeof v==='number'?v.toFixed(4):v }).join(',')
  )
  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a'); link.href=url; link.download=filename; link.click()
  URL.revokeObjectURL(url)
}
