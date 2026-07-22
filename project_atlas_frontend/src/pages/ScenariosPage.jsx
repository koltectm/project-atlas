/**
 * src/pages/ScenariosPage.jsx
 * ==============================
 * Scenario list + management page with My/Public tabs, search, sort.
 */
import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'
import { Plus, Search, FlaskConical } from 'lucide-react'
import toast from 'react-hot-toast'
import { PageHeader } from '@/components/layout/PageHeader.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { Input } from '@/components/ui/Input.jsx'
import { Select } from '@/components/ui/Select.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { ScenarioCard } from '@/components/scenario/ScenarioCard.jsx'
import { useScenarios, useScenarioMutations } from '@/hooks/useScenario.js'
import { simulationService } from '@/services/simulationService.js'
import useSimulationStore from '@/store/simulationStore.js'
import { useAuth } from '@/hooks/useAuth.js'

const SORT_OPTIONS = [
  { label: 'Newest first', value: 'newest' },
  { label: 'Name (A–Z)',   value: 'name' },
]

export function ScenariosPage() {
  const navigate    = useNavigate()
  const { canRunSimulations } = useAuth()
  const [tab, setTab]         = useState('mine')
  const [search, setSearch]   = useState('')
  const [sort, setSort]       = useState('newest')

  const { scenarios, isLoading } = useScenarios(tab)
  const { deleteScenario }       = useScenarioMutations()
  const setActiveRun             = useSimulationStore((s) => s.setActiveRun)

  const filtered = useMemo(() => {
    let result = scenarios
    if (search) {
      const q = search.toLowerCase()
      result = result.filter((s) =>
        s.scenario_name.toLowerCase().includes(q) ||
        s.description?.toLowerCase().includes(q)
      )
    }
    if (sort === 'name') {
      result = [...result].sort((a, b) => a.scenario_name.localeCompare(b.scenario_name))
    } else {
      result = [...result].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    }
    return result
  }, [scenarios, search, sort])

  const handleDelete = async (id) => {
    if (!confirm('Delete this scenario? This cannot be undone.')) return
    deleteScenario.mutate(id)
  }

  const handleRun = async (scenario) => {
    try {
      const { data: run } = await simulationService.run(scenario.scenario_id)
      setActiveRun(run)
      toast.success('Simulation queued')
      navigate(`/simulation/${run.run_id}`)
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to start simulation')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scenarios"
        description="Build and manage Monte Carlo stress-test scenarios"
        actions={
          canRunSimulations && (
            <Button variant="primary" icon={Plus} onClick={() => navigate('/scenarios/new')}>
              New Scenario
            </Button>
          )
        }
      />

      {/* Tabs */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex rounded-lg border border-surface-500 overflow-hidden">
          {[
            { key: 'mine',   label: 'My Scenarios' },
            { key: 'public', label: 'Public Scenarios' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={clsx(
                'px-4 py-2 text-sm font-medium transition-all duration-150',
                tab === key
                  ? 'bg-primary-600/20 text-primary-300'
                  : 'bg-surface-700 text-gray-400 hover:text-gray-200'
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <div className="w-64">
            <Input
              placeholder="Search scenarios…"
              icon={Search}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="w-44">
            <Select
              options={SORT_OPTIONS}
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title={search ? 'No matching scenarios' : 'No scenarios yet'}
          description={
            search
              ? 'Try a different search term.'
              : tab === 'mine'
                ? 'Create your first stress-test scenario to get started.'
                : 'No public scenarios are available yet.'
          }
          action={
            !search && tab === 'mine' && canRunSimulations && (
              <Button variant="primary" icon={Plus} onClick={() => navigate('/scenarios/new')}>
                Create Scenario
              </Button>
            )
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((scenario) => (
            <ScenarioCard
              key={scenario.scenario_id}
              scenario={scenario}
              onDelete={handleDelete}
              onRun={handleRun}
            />
          ))}
        </div>
      )}
    </div>
  )
}
