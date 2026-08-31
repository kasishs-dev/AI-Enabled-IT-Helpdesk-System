import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import TicketTable from '../components/TicketTable'
import PageHeader from '../components/PageHeader'
import { IconSearch } from '../components/Icons'

export default function Tickets() {
  const [tickets, setTickets] = useState([])
  const [q, setQ] = useState('')
  const navigate = useNavigate()

  const load = () => {
    api.get('/tickets', { params: q ? { q } : {} }).then((r) => setTickets(r.data))
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <PageHeader title="Tickets" subtitle="Search and manage IT support tickets" />
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', maxWidth: 480, position: 'relative' }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }}>
          <IconSearch />
        </span>
        <input
          className="search-input"
          placeholder="Search by ID, title, category..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
        />
        <button className="btn btn-secondary" onClick={load}>Search</button>
      </div>
      <TicketTable tickets={tickets} onRowClick={(t) => navigate(`/tickets/${t.id}`)} />
    </div>
  )
}
