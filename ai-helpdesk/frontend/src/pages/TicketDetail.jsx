import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../hooks/useAuth'
import AIBlock from '../components/AIBlock'
import { PriorityBadge, StatusBadge } from '../components/TicketTable'
import LoadingSpinner from '../components/LoadingSpinner'

export default function TicketDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [ticket, setTicket] = useState(null)
  const [comment, setComment] = useState('')
  const [resolution, setResolution] = useState('')

  const load = () => api.get(`/tickets/${id}`).then((r) => setTicket(r.data))
  useEffect(() => { load() }, [id])

  const updateStatus = async (status, extra = {}) => {
    await api.patch(`/tickets/${id}/status`, { status, ...extra })
    load()
  }

  const addComment = async () => {
    if (!comment.trim()) return
    await api.post(`/tickets/${id}/comments`, { content: comment })
    setComment('')
    load()
  }

  if (!ticket) return <LoadingSpinner message="Loading ticket..." />

  const isIT = user.role === 'IT_SUPPORT' || user.role === 'IT_MANAGER'
  const isUser = user.role === 'USER'
  const initials = (name) => name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="ticket-id" style={{ fontSize: '0.875rem', marginBottom: '0.375rem' }}>{ticket.ticket_number}</div>
        <h1 style={{ margin: '0 0 0.75rem', fontSize: '1.5rem', fontWeight: 800 }}>{ticket.title}</h1>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <PriorityBadge severity={ticket.severity} />
          <StatusBadge status={ticket.status} />
          {ticket.category && <span className="badge badge-status">{ticket.category}</span>}
        </div>
      </div>

      <div className="grid ticket-detail-grid" style={{ gridTemplateColumns: '1fr 340px', gap: '1.25rem' }}>
        <div>
          <div className="card" style={{ marginBottom: '1.25rem' }}>
            <h3 className="section-title">Description</h3>
            <p style={{ margin: 0, lineHeight: 1.7, color: 'var(--text-secondary)' }}>{ticket.description}</p>
          </div>

          <AIBlock title="AI Analysis">
            <div className="grid grid-2" style={{ gap: '0.75rem' }}>
              <div><div style={{ color: 'var(--muted)', fontSize: '0.75rem', marginBottom: 2 }}>Summary</div>{ticket.ai_summary}</div>
              <div><div style={{ color: 'var(--muted)', fontSize: '0.75rem', marginBottom: 2 }}>Category</div>{ticket.category} / {ticket.subcategory}</div>
              <div><div style={{ color: 'var(--muted)', fontSize: '0.75rem', marginBottom: 2 }}>Severity</div>{ticket.severity} ({ticket.priority})</div>
              <div><div style={{ color: 'var(--muted)', fontSize: '0.75rem', marginBottom: 2 }}>Confidence</div>{ticket.ai_confidence ? `${(ticket.ai_confidence * 100).toFixed(0)}%` : 'N/A'}</div>
              <div style={{ gridColumn: '1 / -1' }}><div style={{ color: 'var(--muted)', fontSize: '0.75rem', marginBottom: 2 }}>Reasoning</div>{ticket.ai_reasoning}</div>
            </div>
          </AIBlock>

          <div className="card">
            <h3 className="section-title">Comments</h3>
            {ticket.comments?.length === 0 && <div className="empty" style={{ padding: '1.5rem' }}>No comments yet</div>}
            {ticket.comments?.map((c) => (
              <div key={c.id} className="comment-item">
                <div className="comment-meta">
                  <div className="avatar avatar-sm">{initials(c.author?.name)}</div>
                  <span className="comment-author">{c.author?.name || 'User'}</span>
                  <span className="comment-time">{new Date(c.created_at).toLocaleString()}</span>
                </div>
                <p style={{ margin: '0 0 0 2.5rem', color: 'var(--text-secondary)' }}>{c.content}</p>
              </div>
            ))}
            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-light)' }}>
              <textarea className="form-group" value={comment} onChange={(e) => setComment(e.target.value)} rows={3} style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border)', borderRadius: '8px' }} placeholder="Write a comment..." />
              <button className="btn btn-primary btn-sm" style={{ marginTop: '0.5rem' }} onClick={addComment}>Post Comment</button>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <h3 className="section-title">Requester</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="avatar">{initials(ticket.requester?.name)}</div>
              <div>
                <div style={{ fontWeight: 600 }}>{ticket.requester?.name}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>{ticket.requester?.email}</div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="section-title">Assigned Engineer</h3>
            {ticket.assignee ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className="avatar">{initials(ticket.assignee.name)}</div>
                <div style={{ fontWeight: 600 }}>{ticket.assignee.name}</div>
              </div>
            ) : (
              <span style={{ color: 'var(--muted)' }}>Unassigned</span>
            )}
          </div>

          {isIT && (
            <div className="card">
              <h3 className="section-title">Actions</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {ticket.status === 'ASSIGNED' && (
                  <button className="btn btn-primary" onClick={() => updateStatus('IN_PROGRESS')}>Start Work</button>
                )}
                {ticket.status === 'IN_PROGRESS' && (
                  <>
                    <button className="btn btn-secondary" onClick={() => updateStatus('WAITING_FOR_USER')}>Request Information</button>
                    <textarea placeholder="Resolution notes..." value={resolution} onChange={(e) => setResolution(e.target.value)} rows={3} style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border)', borderRadius: '8px' }} />
                    <button className="btn btn-primary" onClick={() => updateStatus('RESOLVED', { resolution_notes: resolution })}>Mark Resolved</button>
                    <button className="btn btn-danger" onClick={() => updateStatus('ESCALATED', { reason: 'Escalated to manager' })}>Escalate</button>
                  </>
                )}
              </div>
            </div>
          )}

          {isUser && ticket.status === 'RESOLVED' && (
            <div className="card">
              <h3 className="section-title">Confirm Resolution</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0 0 1rem' }}>Has your issue been resolved?</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <button className="btn btn-primary" onClick={() => updateStatus('CLOSED')}>Yes — Close Ticket</button>
                <button className="btn btn-secondary" onClick={() => updateStatus('REOPENED', { reason: 'Issue persists' })}>No — Reopen</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
