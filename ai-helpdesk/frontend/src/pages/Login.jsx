import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { IconSparkle } from '../components/Icons'

const DEMO = [
  { name: 'Rahul Sharma', role: 'User', email: 'rahul@demo.com' },
  { name: 'Amit Patel', role: 'IT Support', email: 'amit@demo.com' },
  { name: 'Neha Shah', role: 'IT Manager', email: 'neha@demo.com' },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('rahul@demo.com')
  const [password, setPassword] = useState('Demo@123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (demoEmail) => {
    setEmail(demoEmail)
    setPassword('Demo@123')
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <h1>AI Helpdesk</h1>
        <p>Enterprise IT Service Management powered by intelligent automation. Report issues, get instant AI assistance, and track resolution — all in one place.</p>
        <div className="login-features">
          <div className="login-feature">
            <div className="login-feature-icon"><IconSparkle /></div>
            AI-powered triage & troubleshooting
          </div>
          <div className="login-feature">
            <div className="login-feature-icon">🎯</div>
            Smart ticket routing & assignment
          </div>
          <div className="login-feature">
            <div className="login-feature-icon">📊</div>
            Real-time dashboards & analytics
          </div>
        </div>
      </div>

      <div className="login-form-side">
        <div className="login-card">
          <h2>Welcome back</h2>
          <p className="subtitle">Sign in to your account</p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Email address</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            {error && <div className="alert-error">{error}</div>}
            <button className="btn btn-primary btn-lg" style={{ width: '100%' }} disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="demo-box">
            <strong>Demo accounts — click to fill</strong>
            {DEMO.map((d) => (
              <div key={d.email} className="demo-account" onClick={() => fillDemo(d.email)}>
                <span>{d.name} <span style={{ color: 'var(--muted)' }}>({d.role})</span></span>
                <span>{d.email}</span>
              </div>
            ))}
            <p style={{ margin: '0.5rem 0 0', color: 'var(--muted)' }}>Password: Demo@123</p>
          </div>
        </div>
      </div>
    </div>
  )
}
