import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'unread', label: 'Unread' },
  { id: 'assignments', label: 'Assignments' },
  { id: 'escalations', label: 'Escalations' },
]

export default function Notifications() {
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = () => {
    setLoading(true)
    api.get('/notifications').then((r) => { setItems(r.data); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const markRead = async (id, ticketId) => {
    await api.patch(`/notifications/${id}/read`)
    if (ticketId) navigate(`/tickets/${ticketId}`)
    else load()
  }

  const filtered = items.filter((n) => {
    if (filter === 'unread') return !n.is_read
    if (filter === 'assignments') return n.type === 'TICKET_ASSIGNMENT'
    if (filter === 'escalations') return n.type === 'ESCALATION'
    return true
  })

  return (
    <div>
      <PageHeader title="Notifications" subtitle="Stay updated on ticket assignments and changes" />
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {FILTERS.map((f) => (
          <button key={f.id} className={`btn btn-sm ${filter === f.id ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(f.id)}>
            {f.label}
          </button>
        ))}
      </div>
      {loading ? <LoadingSpinner /> : filtered.map((n) => (
        <div
          key={n.id}
          className={`notif-item ${!n.is_read ? 'unread' : ''}`}
          onClick={() => markRead(n.id, n.ticket_id)}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <strong style={{ fontSize: '0.9375rem' }}>{n.title}</strong>
            {!n.is_read && <span className="badge badge-p2" style={{ fontSize: '0.625rem' }}>NEW</span>}
          </div>
          <p style={{ whiteSpace: 'pre-line', color: 'var(--text-secondary)', margin: '0 0 0.375rem', fontSize: '0.875rem' }}>{n.message}</p>
          <span style={{ color: 'var(--muted)', fontSize: '0.75rem' }}>{new Date(n.created_at).toLocaleString()}</span>
        </div>
      ))}
      {!loading && !filtered.length && <div className="card empty">No notifications</div>}
    </div>
  )
}
