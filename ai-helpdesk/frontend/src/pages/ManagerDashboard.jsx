import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import StatCard from '../components/StatCard'
import TicketTable from '../components/TicketTable'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function ManagerDashboard() {
  const [data, setData] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/dashboard/manager').then((r) => setData(r.data))
  }, [])

  if (!data) return <LoadingSpinner message="Loading operations dashboard..." />

  const maxSeverity = Math.max(...Object.values(data.severity_distribution), 1)
  const maxWorkload = Math.max(...data.team_workload.map((w) => w.active_tickets), 1)

  return (
    <div>
      <PageHeader
        title="Operations Dashboard"
        subtitle="Organization-wide IT metrics, team workload, and AI performance"
      />

      <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard label="Total Tickets" value={data.total_tickets} accent="#6366f1" />
        <StatCard label="Open" value={data.open} accent="#3b82f6" />
        <StatCard label="In Progress" value={data.in_progress} accent="#f59e0b" icon="orange" />
        <StatCard label="Suppressed" value={data.suppressed} accent="#94a3b8" />
      </div>

      <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <h3 className="section-title">Severity Distribution</h3>
          {Object.entries(data.severity_distribution).map(([k, v]) => (
            <div key={k} className="metric-row">
              <span style={{ fontWeight: 600, minWidth: 28 }}>{k}</span>
              <div className="metric-bar-wrap">
                <div className="metric-bar" style={{ width: `${(v / maxSeverity) * 100}%` }} />
              </div>
              <strong>{v}</strong>
            </div>
          ))}
        </div>
        <div className="card">
          <h3 className="section-title">Team Workload</h3>
          {data.team_workload.map((w) => (
            <div key={w.engineer} className="metric-row">
              <span style={{ minWidth: 100 }}>{w.engineer}</span>
              <div className="metric-bar-wrap">
                <div className="metric-bar" style={{ width: `${(w.active_tickets / maxWorkload) * 100}%`, background: 'linear-gradient(90deg, #8b5cf6, #6366f1)' }} />
              </div>
              <strong>{w.active_tickets}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 className="section-title">✨ AI Performance</h3>
        <div className="grid grid-4">
          <StatCard label="Validation Accuracy" value={`${(data.ai_metrics.validation_accuracy * 100).toFixed(0)}%`} accent="#8b5cf6" icon="purple" />
          <StatCard label="Auto Validated" value={data.ai_metrics.auto_validated} accent="#6366f1" />
          <StatCard label="Suppressed" value={data.ai_metrics.suppressed} accent="#f59e0b" icon="orange" />
          <StatCard label="Escalations" value={data.ai_metrics.escalations} accent="#ef4444" icon="red" />
        </div>
      </div>

      <h2 className="section-title">Recent Tickets</h2>
      <TicketTable tickets={data.recent_tickets} onRowClick={(t) => navigate(`/tickets/${t.id}`)} />
    </div>
  )
}
