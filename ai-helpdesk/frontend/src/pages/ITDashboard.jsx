import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import StatCard from '../components/StatCard'
import TicketTable from '../components/TicketTable'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function ITDashboard() {
  const [data, setData] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/dashboard/it').then((r) => setData(r.data))
  }, [])

  if (!data) return <LoadingSpinner message="Loading IT dashboard..." />

  return (
    <div>
      <PageHeader
        title="Support Dashboard"
        subtitle="Manage assigned tickets and track your workload"
      />
      <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard label="Assigned to Me" value={data.assigned_to_me} accent="#6366f1" />
        <StatCard label="P1 / P2 Tickets" value={data.high_priority} accent="#ef4444" icon="red" />
        <StatCard label="In Progress" value={data.in_progress} accent="#f59e0b" icon="orange" />
        <StatCard label="Resolved Today" value={data.resolved_today} accent="#10b981" icon="green" />
      </div>
      <h2 className="section-title">My Tickets</h2>
      <TicketTable tickets={data.tickets} onRowClick={(t) => navigate(`/tickets/${t.id}`)} />
    </div>
  )
}
