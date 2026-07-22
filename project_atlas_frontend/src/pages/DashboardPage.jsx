/**
 * src/pages/DashboardPage.jsx
 * =============================
 * Main overview dashboard — quick stats, recent scenarios, recent runs.
 */
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  FlaskConical, Play, Network as NetworkIcon, ArrowRight,
  Activity, Database, Layers,
} from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader.jsx'
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { StatusBadge } from '@/components/ui/Badge.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { useAuth } from '@/hooks/useAuth.js'
import { useScenarios } from '@/hooks/useScenario.js'
import { nodeService } from '@/services/nodeService.js'
import { formatRelative } from '@/utils/formatters.js'

export function DashboardPage() {
  const { profile } = useAuth()
  const { scenarios, isLoading: scenariosLoading } = useScenarios('mine')

  const { data: nodeData } = useQuery({
    queryKey: ['nodes-summary'],
    queryFn:  () => nodeService.getAll({ limit: 1 }).then((r) => r.data),
    staleTime: 5 * 60_000,
  })

  const recentScenarios = scenarios.slice(0, 5)

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${profile?.full_name?.split(' ')[0] || 'there'}`}
        description="Here's an overview of your supply chain stress-testing workspace."
      />

      {/* Quick action cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to="/network">
          <Card hover className="h-full">
            <CardBody className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-primary-900/40 border border-primary-700/40
                              flex items-center justify-center flex-shrink-0">
                <NetworkIcon className="w-5 h-5 text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">Explore Network</p>
                <p className="text-xs text-gray-500">View the supply chain map</p>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
            </CardBody>
          </Card>
        </Link>

        <Link to="/scenarios/new">
          <Card hover className="h-full">
            <CardBody className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-accent-500/20 border border-accent-500/40
                              flex items-center justify-center flex-shrink-0">
                <FlaskConical className="w-5 h-5 text-accent-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">New Scenario</p>
                <p className="text-xs text-gray-500">Build a stress-test scenario</p>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
            </CardBody>
          </Card>
        </Link>

        <Link to="/analytics">
          <Card hover className="h-full">
            <CardBody className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-amber-900/30 border border-amber-700/40
                              flex items-center justify-center flex-shrink-0">
                <Activity className="w-5 h-5 text-amber-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">OR Analytics</p>
                <p className="text-xs text-gray-500">Critical path & vulnerability</p>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
            </CardBody>
          </Card>
        </Link>
      </div>

      {/* Recent scenarios */}
      <Card>
        <CardHeader action={
          <Link to="/scenarios">
            <Button variant="ghost" size="sm" iconRight={ArrowRight}>View all</Button>
          </Link>
        }>
          <CardTitle>Recent Scenarios</CardTitle>
        </CardHeader>
        <CardBody>
          {scenariosLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 bg-surface-700 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : recentScenarios.length === 0 ? (
            <EmptyState
              icon={FlaskConical}
              title="No scenarios yet"
              description="Create your first stress-test scenario to get started."
              action={
                <Link to="/scenarios/new">
                  <Button variant="primary" icon={FlaskConical}>Create Scenario</Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-2">
              {recentScenarios.map((s) => (
                <Link
                  key={s.scenario_id}
                  to={`/scenarios/${s.scenario_id}`}
                  className="flex items-center justify-between rounded-lg border border-surface-500
                             bg-surface-700 hover:bg-surface-600 transition-colors px-4 py-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Layers className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate">{s.scenario_name}</p>
                      <p className="text-xs text-gray-500">
                        {s.disruptions?.length || 0} disruptions · {formatRelative(s.updated_at)}
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={s.status} />
                </Link>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
