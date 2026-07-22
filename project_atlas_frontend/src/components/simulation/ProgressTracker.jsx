import { useNavigate } from 'react-router-dom'
import { AlertCircle, CheckCircle2, Clock, RefreshCw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { CircularProgress } from '@/components/ui/ProgressBar.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { StatusBadge } from '@/components/ui/Badge.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { useSimulation } from '@/hooks/useSimulation.js'
import { formatIterations, formatSeconds } from '@/utils/formatters.js'

export function ProgressTracker({ runId }) {
  const navigate = useNavigate()
  const { run, error, progressPct, status, isCompleted, isFailed } = useSimulation(runId, { autoNavigate: true })

  if (error) return <AlertBanner variant="error" title="Could not load simulation status">{error.message}</AlertBanner>
  if (!run) return <div className="flex items-center justify-center py-24"><div className="flex flex-col items-center gap-3"><RefreshCw className="w-8 h-8 text-gray-500 animate-spin"/><p className="text-sm text-gray-400">Connecting to simulation…</p></div></div>

  return (
    <div className="flex flex-col items-center gap-8 py-8">
      <StatusBadge status={status}/>
      <AnimatePresence mode="wait">
        {isCompleted
          ? <motion.div key="complete" initial={{scale:0.8,opacity:0}} animate={{scale:1,opacity:1}} className="flex flex-col items-center gap-3">
              <div className="w-40 h-40 rounded-full bg-green-900/20 border-4 border-green-500 flex items-center justify-center"><CheckCircle2 className="w-16 h-16 text-green-400"/></div>
              <p className="text-green-400 font-semibold">Simulation Complete</p>
              <p className="text-sm text-gray-400">Redirecting to results…</p>
            </motion.div>
          : isFailed
          ? <motion.div key="failed" initial={{scale:0.8,opacity:0}} animate={{scale:1,opacity:1}} className="flex flex-col items-center gap-3">
              <div className="w-40 h-40 rounded-full bg-red-900/20 border-4 border-red-500 flex items-center justify-center"><AlertCircle className="w-16 h-16 text-red-400"/></div>
              <p className="text-red-400 font-semibold">Simulation Failed</p>
            </motion.div>
          : <motion.div key="progress" initial={{opacity:0}} animate={{opacity:1}}>
              <CircularProgress value={progressPct} size={200} strokeWidth={10}/>
            </motion.div>}
      </AnimatePresence>
      {!isCompleted && !isFailed && (
        <div className="text-center">
          <p className="text-lg font-mono font-bold text-white tabular-nums">
            {formatIterations(run.completed_iterations)}<span className="text-gray-500 font-normal"> / {formatIterations(run.total_iterations)}</span>
          </p>
          <p className="text-sm text-gray-400 mt-1">iterations complete</p>
        </div>
      )}
      <div className="grid grid-cols-3 gap-4 w-full max-w-md">
        <Card><CardBody className="text-center py-3"><Clock className="w-4 h-4 text-gray-500 mx-auto mb-1"/><p className="text-xs text-gray-500">Duration</p><p className="text-sm font-mono font-bold text-white">{run.duration_seconds!=null?formatSeconds(run.duration_seconds):'—'}</p></CardBody></Card>
        <Card><CardBody className="text-center py-3"><p className="text-xs text-gray-500 mb-1">Run ID</p><p className="text-xs font-mono text-gray-300 truncate">{run.run_id?.slice(0,8)}…</p></CardBody></Card>
        <Card><CardBody className="text-center py-3"><p className="text-xs text-gray-500 mb-1">Engine</p><p className="text-sm font-mono font-bold text-white">{run.engine_version||'1.0.0'}</p></CardBody></Card>
      </div>
      {isFailed && run.error_message && <AlertBanner variant="error" title="Error details" className="w-full max-w-xl"><p className="font-mono text-xs break-all">{run.error_message}</p></AlertBanner>}
      {isFailed  && <Button variant="secondary" onClick={()=>navigate('/scenarios')}>Back to Scenarios</Button>}
      {isCompleted && <Button variant="primary" onClick={()=>navigate(`/results/${runId}`)}>View Results Now</Button>}
    </div>
  )
}
