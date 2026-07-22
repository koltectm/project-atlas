export function buildHistogram(values, nBins=50) {
  if (!values?.length) return []
  const min=Math.min(...values), max=Math.max(...values)
  if (min===max) return [{bin_start:min,bin_end:max,bin_mid:min,count:values.length}]
  const binWidth=(max-min)/nBins
  const bins=Array.from({length:nBins},(_,i)=>({
    bin_start:min+i*binWidth, bin_end:min+(i+1)*binWidth,
    bin_mid:min+(i+0.5)*binWidth, count:0,
  }))
  values.forEach((v)=>{ const idx=Math.min(Math.floor((v-min)/binWidth),nBins-1); bins[idx].count++ })
  return bins
}
export function buildCDF(values, nPoints=200) {
  if (!values?.length) return []
  const sorted=[...values].sort((a,b)=>a-b), n=sorted.length
  const step=Math.max(1,Math.floor(n/nPoints))
  return sorted.filter((_,i)=>i%step===0||i===n-1).map((v)=>({value:v,cdf:(sorted.indexOf(v)+1)/n}))
}
export function keyedAggregates(aggregates=[]) {
  return Object.fromEntries(aggregates.map((a)=>[a.metric_name,a]))
}
export function buildComparisonData(comparison, label1='Run 1', label2='Run 2') {
  if (!comparison?.metrics) return []
  return Object.entries(comparison.metrics).map(([metric,vals])=>({
    metric, [label1]:vals.run_1_mean, [label2]:vals.run_2_mean, delta_pct:vals.delta_pct,
  }))
}
export function rgba(hex, alpha) {
  const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16)
  return `rgba(${r},${g},${b},${alpha})`
}
