/**
 * src/pages/AnalyticsPage.jsx
 * ==============================
 * System-wide OR analytics: critical path, network validation, mitigation optimiser.
 * Not tied to a specific simulation run — operates on the static network topology.
 */
import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader.jsx'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { Badge } from '@/components/ui/Badge.jsx'
import { CriticalPathViz } from '@/components/results/CriticalPathViz.jsx'
import { MitigationPanel } from '@/components/results/MitigationPanel.jsx'
import { analyticsService } from '@/services/analyticsService.js'

function NetworkValidationCard() {
  const { data, isLoading } = useQuery({
    queryKey: ['network-validation'],
    queryFn:  () => analyticsService.validateNetwork().then((r) => r.data),
    staleTime: 5 * 60_000,
  })

  if (isLoading) {
    return (
      <Card className="h-32 flex items-center justify-center">
        <Spinner />
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Network Connectivity</CardTitle>
        <CardDescription>Graph validation results for the supply chain topology</CardDescription>
      </CardHeader>
      <CardBody className="space-y-4">
        <div className="flex items-center gap-2">
          {data?.is_valid ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-green-400" />
              <span className="text-sm font-medium text-green-400">Network graph is valid</span>
            </>
          ) : (
            <>
              <XCircle className="w-5 h-5 text-red-400" />
              <span className="text-sm font-medium text-red-400">Network graph has issues</span>
            </>
          )}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-2xs text-gray-500">Nodes</p>
            <p className="text-lg font-mono font-bold text-white">{data?.n_nodes ?? '—'}</p>
          </div>
          <div>
            <p className="text-2xs text-gray-500">Edges</p>
            <p className="text-lg font-mono font-bold text-white">{data?.n_edges ?? '—'}</p>
          </div>
          <div>
            <p className="text-2xs text-gray-500">Components</p>
            <p className="text-lg font-mono font-bold text-white">
              {data?.n_weakly_connected_components ?? '—'}
            </p>
          </div>
        </div>

        {data?.errors?.length > 0 && (
          <AlertBanner variant="error" title="Validation errors">
            <ul className="list-disc list-inside space-y-1">
              {data.errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </AlertBanner>
        )}

        {data?.warnings?.length > 0 && (
          <AlertBanner variant="warning" title="Warnings">
            <ul className="list-disc list-inside space-y-1">
              {data.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </AlertBanner>
        )}
      </CardBody>
    </Card>
  )
}

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics & OR Engine"
        description="Network-wide Operations Research analysis — independent of any single simulation run"
      />

      <NetworkValidationCard />

      <CriticalPathViz />

      <MitigationPanel />
    </div>
  )
}
