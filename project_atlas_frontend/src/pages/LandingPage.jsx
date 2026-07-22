/**
 * src/pages/LandingPage.jsx
 * ===========================
 * Public-facing landing page. No auth required.
 */
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ShieldAlert, ArrowRight, Database, Activity, Network as NetworkIcon,
  Zap, BarChart3, Globe, CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/Button.jsx'
import { APP_NAME } from '@/config/constants.js'

const FEATURES = [
  {
    Icon: Zap,
    title: 'Monte Carlo Engine',
    desc: '10,000 stochastic iterations in 0.09 seconds using fully vectorised NumPy — 668× faster than the 60-second target.',
  },
  {
    Icon: Activity,
    title: 'Real-time Simulation',
    desc: 'Live progress tracking as the simulation engine samples disruptions, computes flow, and calculates risk metrics.',
  },
  {
    Icon: BarChart3,
    title: 'Operations Research Analysis',
    desc: 'Critical path analysis, max-flow/min-cut, betweenness centrality, and ILP mitigation optimisation via PuLP/CBC.',
  },
  {
    Icon: Database,
    title: 'Nigerian Oil & Gas Data',
    desc: '40 real supply chain nodes and 52 links modelling wellheads, refineries, pipelines, ports, and distribution networks.',
  },
]

const STATS = [
  { value: '40+',     label: 'Supply Chain Nodes' },
  { value: '25+',     label: 'Disruption Types' },
  { value: '10,000',  label: 'Iterations in 0.09s' },
  { value: '8',       label: 'Disruption Categories' },
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-surface-900 bg-grid overflow-x-hidden">
      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 lg:px-12 py-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <ShieldAlert className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="text-base font-bold text-white">{APP_NAME}</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/auth">
            <Button variant="ghost" size="sm">Sign in</Button>
          </Link>
          <Link to="/auth">
            <Button variant="primary" size="sm">Get Started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative px-6 lg:px-12 pt-20 pb-24 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                           bg-primary-900/40 border border-primary-700/50 text-primary-300 text-xs font-medium mb-6">
            <Globe className="w-3 h-3" />
            Nigerian Oil & Gas Supply Chain
          </span>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight">
            Stress-Test Any
            <br />
            <span className="text-gradient">Supply Chain Disruption</span>
          </h1>

          <p className="mt-6 text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            A stochastic Monte Carlo simulation system modelling the full Nigerian oil & gas
            supply chain — from wellheads to retail stations — under configurable disruption
            scenarios, with rigorous Operations Research analysis.
          </p>

          <div className="mt-9 flex items-center justify-center gap-4 flex-wrap">
            <Link to="/auth">
              <Button variant="primary" size="lg" iconRight={ArrowRight}>
                Get Started Free
              </Button>
            </Link>
            <Link to="/auth">
              <Button variant="secondary" size="lg">
                View Demo
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Animated supply chain flow diagram */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mt-16 relative"
        >
          <div className="flex items-center justify-center gap-3 sm:gap-6 flex-wrap">
            {['Wellhead', 'Pipeline', 'Terminal', 'Refinery', 'Depot', 'Consumer'].map((stage, i) => (
              <div key={stage} className="flex items-center gap-3 sm:gap-6">
                <div className="flex flex-col items-center gap-2">
                  <div
                    className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-surface-700 border-2 border-primary-600/50
                               flex items-center justify-center animate-pulse-slow"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  >
                    <NetworkIcon className="w-5 h-5 text-primary-400" />
                  </div>
                  <span className="text-2xs text-gray-500">{stage}</span>
                </div>
                {i < 5 && (
                  <svg width="32" height="8" className="hidden sm:block flex-shrink-0">
                    <line
                      x1="0" y1="4" x2="32" y2="4"
                      stroke="#3b82f6" strokeWidth="2"
                      strokeDasharray="4 4"
                      className="animate-flow-right"
                    />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Stats row */}
      <section className="px-6 lg:px-12 py-12 border-y border-surface-500 bg-surface-800/50">
        <div className="max-w-5xl mx-auto grid grid-cols-2 lg:grid-cols-4 gap-8">
          {STATS.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-3xl font-mono font-bold text-gradient">{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-6 lg:px-12 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-white">Built for Rigorous Analysis</h2>
          <p className="text-gray-400 mt-2">
            Production-grade simulation infrastructure suitable for academic publication
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {FEATURES.map(({ Icon, title, desc }) => (
            <div
              key={title}
              className="rounded-xl border border-surface-500 bg-surface-800 p-6
                         hover:border-primary-600/50 transition-all duration-200"
            >
              <div className="w-10 h-10 rounded-lg bg-primary-900/40 border border-primary-700/40
                              flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 text-primary-400" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">{title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 lg:px-12 py-10 border-t border-surface-500">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-500">
            {APP_NAME} — Stochastic Supply Chain Stress-Testing System
          </p>
          <p className="text-xs text-gray-600">
            Targeting publication in the International Journal of Production Economics
          </p>
        </div>
      </footer>
    </div>
  )
}
