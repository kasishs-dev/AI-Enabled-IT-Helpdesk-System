import { useEffect, useState } from 'react'
import api from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Team() {
  const [team, setTeam] = useState([])

  useEffect(() => {
    api.get('/team').then((r) => setTeam(r.data))
  }, [])

  if (!team.length) return <LoadingSpinner message="Loading team..." />

  return (
    <div>
      <PageHeader title="IT Team" subtitle="Engineer expertise, availability, and capacity" />
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
        {team.map((p) => (
          <div key={p.id} className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', marginBottom: '1rem' }}>
              <div className="avatar">
                {p.user?.name?.split(' ').map((n) => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>{p.user?.name}</h3>
                <div style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>{p.user?.email}</div>
              </div>
            </div>
            <div style={{ fontSize: '0.875rem' }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ color: 'var(--muted)', fontSize: '0.75rem', marginBottom: 4 }}>Expertise</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                  {(p.expertise || []).map((e) => (
                    <span key={e} className="badge badge-status">{e}</span>
                  ))}
                </div>
              </div>
              <div className="metric-row">
                <span>Max tickets</span><strong>{p.max_active_tickets}</strong>
              </div>
              <div className="metric-row">
                <span>Available</span>
                <span className={`badge ${p.availability ? 'badge-resolved' : 'badge-escalated'}`}>
                  {p.availability ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
