/**
 * src/components/results/MitigationPanel.jsx
 * ============================================
 * Displays the ILP mitigation optimisation results.
 * Allows user to trigger optimisation with budget/effectiveness parameters.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Shield, DollarSign, TrendingUp, CheckCircle2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { Badge } from '@/components/ui/Badge.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { analyticsService } from '@/services/analyticsService.js'
import { formatUSD, formatPct, formatScore } from '@/utils/formatters.js'

export function MitigationPanel() {
  const [mode, setMode]                       = useState('min_cost')
  const [targetEffectiveness, setEffective]   = useState(0.60)
  const [budgetUsd, setBudget]                = useState(500_000_000)
  const [result, setResult]                   = useState(null)

  const optimise = useMutation({
    mutationFn: () =>
      analyticsService.optimiseMitigations({
        mode,
        target_effectiveness: targetEffectiveness,
        ...(mode === 'max_effect' ? { budget_usd: budgetUsd } : {}),
      }).then((r) => r.data),
    onSuccess: (data) => setResult(data),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mitigation Strategy Optimiser</CardTitle>
        <CardDescription>
          Integer Linear Programme selecting the optimal set of interventions
          from the strategy catalogue (CBC/COIN solver via PuLP)
        </CardDescription>
      </CardHeader>
      <CardBody className="space-y-5">
        {/* Mode toggle */}
        <div className="flex rounded-lg border border-surface-500 overflow-hidden text-sm w-fit">
          {[
            { value: 'min_cost',   label: 'Minimise Cost' },
            { value: 'max_effect', label: 'Maximise Effectiveness' },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => { setMode(value); setResult(null) }}
              className={`px-4 py-2 font-medium transition-all duration-150 ${
                mode === value
                  ? 'bg-primary-600/20 text-primary-300 border-r border-primary-600/40'
                  : 'bg-surface-700 text-gray-400 hover:text-gray-200 border-r border-surface-500'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Parameters */}
        <div className="grid grid-cols-2 gap-6 max-w-lg">
          {mode === 'min_cost' && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Minimum effectiveness target</span>
                <span className="font-mono text-white">{formatPct(targetEffectiveness)}</span>
              </div>
              <input
                type="range" min={0.1} max={1.0} step={0.05}
                value={targetEffectiveness}
                onChange={(e) => { setEffective(parseFloat(e.target.value)); setResult(null) }}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer
                           bg-surface-600 accent-primary-500"
              />
              <div className="flex justify-between text-2xs text-gray-600">
                <span>10%</span><span>50%</span><span>100%</span>
              </div>
            </div>
          )}

          {mode === 'max_effect' && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Budget ceiling</span>
                <span className="font-mono text-white">{formatUSD(budgetUsd)}</span>
              </div>
              <input
                type="range"
                min={10_000_000} max={5_000_000_000} step={10_000_000}
                value={budgetUsd}
                onChange={(e) => { setBudget(parseInt(e.target.value, 10)); setResult(null) }}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer
                           bg-surface-600 accent-primary-500"
              />
              <div className="flex justify-between text-2xs text-gray-600">
                <span>$10M</span><span>$500M</span><span>$5B</span>
              </div>
            </div>
          )}
        </div>

        <Button
          variant="primary"
          icon={Shield}
          loading={optimise.isPending}
          onClick={() => optimise.mutate()}
        >
          {optimise.isPending ? 'Optimising…' : 'Run ILP Optimisation'}
        </Button>

        {/* Results */}
        {optimise.isError && (
          <AlertBanner variant="error">
            {optimise.error?.response?.data?.message || 'Optimisation failed. Check that mitigation strategies are loaded.'}
          </AlertBanner>
        )}

        {result && (
          <div className="space-y-4 animate-fade-in">
            {/* Status */}
            <div className="flex items-center gap-2">
              {result.status === 'Optimal' ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-medium text-green-400">Optimal solution found</span>
                </>
              ) : (
                <AlertBanner variant="warning">
                  Solver status: {result.status}. No feasible solution found for these constraints.
                </AlertBanner>
              )}
            </div>

            {result.status === 'Optimal' && (
              <>
                {/* Summary metrics */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-surface-700 rounded-xl p-4 text-center">
                    <DollarSign className="w-5 h-5 text-primary-400 mx-auto mb-2" />
                    <p className="text-2xs text-gray-500 mb-1">Total Cost</p>
                    <p className="text-base font-mono font-bold text-white">
                      {formatUSD(result.total_cost_usd)}
                    </p>
                  </div>
                  <div className="bg-surface-700 rounded-xl p-4 text-center">
                    <TrendingUp className="w-5 h-5 text-green-400 mx-auto mb-2" />
                    <p className="text-2xs text-gray-500 mb-1">Effectiveness</p>
                    <p className="text-base font-mono font-bold text-green-400">
                      {formatPct(result.total_effectiveness)}
                    </p>
                  </div>
                  <div className="bg-surface-700 rounded-xl p-4 text-center">
                    <Shield className="w-5 h-5 text-amber-400 mx-auto mb-2" />
                    <p className="text-2xs text-gray-500 mb-1">Prob. Reduction</p>
                    <p className="text-base font-mono font-bold text-amber-400">
                      {formatPct(result.total_probability_reduction)}
                    </p>
                  </div>
                </div>

                {/* Selected strategies */}
                {result.cost_breakdown?.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-white mb-3">
                      Selected Strategies ({result.selected_strategies.length})
                    </p>
                    <div className="space-y-2">
                      {result.cost_breakdown.map((s) => (
                        <div
                          key={s.strategy_id}
                          className="flex items-center justify-between rounded-lg border border-surface-500
                                     bg-surface-700 px-4 py-3"
                        >
                          <div>
                            <p className="text-sm font-medium text-white">{s.strategy_name}</p>
                            <p className="text-xs text-gray-400 mt-0.5">
                              Effectiveness: {formatPct(s.effectiveness_score)}
                              {' · '}
                              Prob reduction: {formatPct(s.reduces_probability_by)}
                            </p>
                          </div>
                          <span className="text-sm font-mono font-bold text-primary-300 flex-shrink-0 ml-4">
                            {formatUSD(s.implementation_cost_usd)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  )
}
