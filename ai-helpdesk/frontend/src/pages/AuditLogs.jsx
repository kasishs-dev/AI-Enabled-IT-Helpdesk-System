import { useEffect, useState } from 'react'
import api from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function AuditLogs() {
  const [logs, setLogs] = useState([])

  useEffect(() => {
    api.get('/audit-logs').then((r) => setLogs(r.data))
  }, [])

  if (!logs.length) return <LoadingSpinner message="Loading audit logs..." />

  return (
    <div>
      <PageHeader title="Audit Logs" subtitle="Track all system events and manager overrides" />
      <div className="card-flat">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Time</th><th>Action</th><th>Entity</th><th>Change</th><th>Reason</th></tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td style={{ color: 'var(--muted)', fontSize: '0.8125rem', whiteSpace: 'nowrap' }}>{new Date(l.created_at).toLocaleString()}</td>
                  <td style={{ fontWeight: 600 }}>{l.action}</td>
                  <td><span className="badge badge-status">{l.entity_type} #{l.entity_id}</span></td>
                  <td style={{ fontSize: '0.8125rem' }}>
                    {l.old_value && <span style={{ color: 'var(--muted)' }}>{l.old_value} → </span>}
                    <span>{l.new_value || '—'}</span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{l.reason || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
