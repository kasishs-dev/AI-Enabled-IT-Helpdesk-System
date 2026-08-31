import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../services/api'
import StatCard from '../components/StatCard'
import TicketTable from '../components/TicketTable'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function UserDashboard() {
  const [data, setData] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/dashboard/user').then((r) => setData(r.data))
  }, [])

  if (!data) return <LoadingSpinner message="Loading your dashboard..." />

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${data.welcome_name}`}
        subtitle="Track your IT requests and get support when you need it"
        action={
          <Link to="/report" className="btn btn-primary btn-lg">
            + Report an IT Problem
          </Link>
        }
      />
      <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard label="Open Tickets" value={data.open_tickets} accent="#6366f1" icon="blue" />
        <StatCard label="In Progress" value={data.in_progress} accent="#f59e0b" icon="orange" />
        <StatCard label="Waiting for You" value={data.waiting_for_user} accent="#8b5cf6" icon="purple" />
        <StatCard label="Resolved" value={data.resolved} accent="#10b981" icon="green" />
      </div>
      <h2 className="section-title">Recent Tickets</h2>
      <TicketTable tickets={data.recent_tickets} onRowClick={(t) => navigate(`/tickets/${t.id}`)} />
    </div>
  )
}
