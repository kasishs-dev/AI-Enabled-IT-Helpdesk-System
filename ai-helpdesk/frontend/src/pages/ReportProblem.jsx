import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import AIBlock from '../components/AIBlock'
import PageHeader from '../components/PageHeader'

const STEPS = [
  'Understanding the problem',
  'Checking for similar issues',
  'Validating the request',
  'Determining priority',
  'Finding the appropriate IT specialist',
]

export default function ReportProblem() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '', description: '', device: '', operating_system: '', location: '', application_system: '',
  })
  const [processing, setProcessing] = useState(false)
  const [step, setStep] = useState(-1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setProcessing(true)
    setResult(null)
    setError('')
    for (let i = 0; i < STEPS.length; i++) {
      setStep(i)
      await new Promise((r) => setTimeout(r, 400))
    }
    try {
      const { data } = await api.post('/issues/create', form)
      setResult(data)
    } catch {
      setError('Failed to submit issue. Please try again.')
    } finally {
      setProcessing(false)
      setStep(STEPS.length)
    }
  }

  if (result) {
    return (
      <div>
        <PageHeader title="Submission Result" subtitle="AI analysis complete" />
        {result.ticket_created ? (
          <div className="card result-success" style={{ marginBottom: '1.25rem' }}>
            <h2 style={{ margin: '0 0 1rem', fontSize: '1.25rem' }}>Ticket created successfully</h2>
            <div className="grid grid-2">
              <div><span style={{ color: 'var(--muted)', fontSize: '0.8125rem' }}>Ticket ID</span><div className="ticket-id" style={{ fontSize: '1.25rem' }}>{result.ticket.ticket_number}</div></div>
              <div><span style={{ color: 'var(--muted)', fontSize: '0.8125rem' }}>Priority</span><div style={{ fontWeight: 700 }}>{result.analysis.severity} — {result.analysis.priority}</div></div>
              <div><span style={{ color: 'var(--muted)', fontSize: '0.8125rem' }}>Assigned to</span><div style={{ fontWeight: 600 }}>{result.ticket.assignee?.name || 'IT Queue'}</div></div>
            </div>
            <p style={{ margin: '1rem 0', color: 'var(--text-secondary)' }}>Our IT team will get back to you shortly.</p>
            <button className="btn btn-primary" onClick={() => navigate(`/tickets/${result.ticket.id}`)}>View Ticket</button>
          </div>
        ) : (
          <div className="card result-warning" style={{ marginBottom: '1.25rem' }}>
            <h2 style={{ margin: '0 0 0.75rem', fontSize: '1.25rem' }}>No ticket created</h2>
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{result.message}</p>
            {result.duplicate_ticket_number && <p style={{ marginTop: '0.5rem' }}><strong>Existing:</strong> {result.duplicate_ticket_number}</p>}
          </div>
        )}
        <AIBlock title="AI Analysis">
          <div className="grid grid-2">
            <div><strong>Category</strong><br />{result.analysis.category || result.analysis.summary}</div>
            {result.analysis.severity && <div><strong>Severity</strong><br />{result.analysis.severity}</div>}
            {result.analysis.confidence && <div><strong>Confidence</strong><br />{(result.analysis.confidence * 100).toFixed(0)}%</div>}
          </div>
        </AIBlock>
        <AIBlock title="AI Suggested Troubleshooting">
          <ol style={{ margin: '0 0 1rem', paddingLeft: '1.25rem' }}>
            {result.suggestions.map((s, i) => <li key={i} style={{ marginBottom: '0.375rem' }}>{s}</li>)}
          </ol>
          <p style={{ margin: 0, fontWeight: 600, fontSize: '0.875rem' }}>Our IT team will get back to you if further assistance is required.</p>
        </AIBlock>
        <button className="btn btn-secondary" onClick={() => { setResult(null); setStep(-1) }}>Submit Another Issue</button>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Report an IT Problem"
        subtitle="Describe your issue — AI will analyze, suggest fixes, and route to IT if needed"
      />

      {processing && (
        <div className="card" style={{ marginBottom: '1.25rem' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Analyzing your issue...</h3>
          <ul className="steps-list">
            {STEPS.map((s, i) => (
              <li key={s} className={`step-item ${i < step ? 'done' : ''} ${i === step ? 'active' : ''}`}>
                <span className="step-dot">{i < step ? '✓' : i + 1}</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label>Problem Title *</label>
          <input name="title" value={form.title} onChange={handleChange} placeholder="e.g. VPN is not connecting" required minLength={3} />
        </div>
        <div className="form-group">
          <label>Problem Description *</label>
          <textarea name="description" value={form.description} onChange={handleChange} rows={6} required minLength={10}
            placeholder="Describe what happened, any error messages, and steps you've already tried..." />
        </div>
        <div className="grid grid-2">
          <div className="form-group"><label>Device</label><input name="device" value={form.device} onChange={handleChange} placeholder="Laptop, Desktop..." /></div>
          <div className="form-group"><label>Operating System</label><input name="operating_system" value={form.operating_system} onChange={handleChange} placeholder="Windows 11, macOS..." /></div>
          <div className="form-group"><label>Location</label><input name="location" value={form.location} onChange={handleChange} placeholder="Office, Remote..." /></div>
          <div className="form-group"><label>Application / System</label><input name="application_system" value={form.application_system} onChange={handleChange} placeholder="VPN Client, Outlook..." /></div>
        </div>
        {error && <div className="alert-error">{error}</div>}
        <button className="btn btn-primary btn-lg" type="submit" disabled={processing}>
          {processing ? 'Processing...' : 'Submit Issue'}
        </button>
      </form>
    </div>
  )
}
