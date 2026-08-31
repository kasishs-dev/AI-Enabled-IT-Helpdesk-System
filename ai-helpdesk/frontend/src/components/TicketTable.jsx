const STATUS_CLASS = {
  OPEN: 'badge-open',
  ASSIGNED: 'badge-assigned',
  IN_PROGRESS: 'badge-in_progress',
  WAITING_FOR_USER: 'badge-waiting_for_user',
  RESOLVED: 'badge-resolved',
  CLOSED: 'badge-closed',
  ESCALATED: 'badge-escalated',
  REOPENED: 'badge-open',
  SUPPRESSED: 'badge-status',
  REJECTED: 'badge-escalated',
}

export function PriorityBadge({ severity }) {
  const cls = severity ? `badge badge-${severity.toLowerCase()}` : 'badge badge-status'
  return <span className={cls}>{severity || 'N/A'}</span>
}

export function StatusBadge({ status }) {
  const cls = STATUS_CLASS[status] || 'badge-status'
  const label = status?.replace(/_/g, ' ') || 'Unknown'
  return <span className={`badge ${cls}`}>{label}</span>
}

export default function TicketTable({ tickets, onRowClick }) {
  if (!tickets?.length) {
    return (
      <div className="card-flat">
        <div className="empty">No tickets found.</div>
      </div>
    )
  }

  return (
    <div className="card-flat">
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Title</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Requester</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr
                key={t.id}
                className={onRowClick ? 'clickable' : ''}
                onClick={() => onRowClick?.(t)}
              >
                <td><span className="ticket-id">{t.ticket_number}</span></td>
                <td style={{ fontWeight: 500 }}>{t.title}</td>
                <td><span className="badge badge-status">{t.category || '—'}</span></td>
                <td><PriorityBadge severity={t.severity} /></td>
                <td><StatusBadge status={t.status} /></td>
                <td style={{ color: 'var(--text-secondary)' }}>{t.requester?.name || '—'}</td>
                <td style={{ color: 'var(--muted)', fontSize: '0.8125rem' }}>
                  {new Date(t.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
