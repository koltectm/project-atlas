/**
 * src/components/results/ExportPanel.jsx
 * ========================================
 * Export controls: PDF report, CSV aggregates, CSV vulnerability data.
 */
import { FileDown, Table, ImageDown } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { useExport } from '@/hooks/useExport.js'

export function ExportPanel({ runId, aggregates, vulnerability, scenarioName }) {
  const { isExporting, exportPdf, exportCsv, exportVulnerabilityToCsv } = useExport()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Export Results</CardTitle>
        <CardDescription>
          Generate publication-ready exports for the IJPE paper or further analysis
        </CardDescription>
      </CardHeader>
      <CardBody>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="primary"
            icon={FileDown}
            loading={isExporting}
            onClick={() => exportPdf(runId, aggregates, scenarioName)}
          >
            Full PDF Report
          </Button>
          <Button
            variant="secondary"
            icon={Table}
            loading={isExporting}
            onClick={() => exportCsv(aggregates, `atlas-aggregates-${runId}.csv`)}
          >
            Aggregates CSV
          </Button>
          <Button
            variant="secondary"
            icon={Table}
            loading={isExporting}
            onClick={() => exportVulnerabilityToCsv(vulnerability, `atlas-vulnerability-${runId}.csv`)}
          >
            Vulnerability CSV
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          PDF reports include statistical summary tables and chart images at 2× resolution
          suitable for academic publication.
        </p>
      </CardBody>
    </Card>
  )
}
