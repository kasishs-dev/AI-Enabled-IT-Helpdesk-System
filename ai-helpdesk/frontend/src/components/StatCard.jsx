const ICONS = {
  blue: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  orange: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  purple: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
    </svg>
  ),
  green: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  red: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    </svg>
  ),
}

const BG = {
  blue: 'rgba(99, 102, 241, 0.12)',
  orange: 'rgba(245, 158, 11, 0.12)',
  purple: 'rgba(139, 92, 246, 0.12)',
  green: 'rgba(16, 185, 129, 0.12)',
  red: 'rgba(239, 68, 68, 0.12)',
}

export default function StatCard({ label, value, accent, icon = 'blue' }) {
  const colorKey = accent === '#dc2626' || accent === '#ef4444' ? 'red'
    : accent === '#d97706' || accent === '#f59e0b' ? 'orange'
    : accent === '#059669' || accent === '#10b981' ? 'green'
    : accent === '#7c3aed' || accent === '#8b5cf6' ? 'purple'
    : icon

  return (
    <div className="card stat-card" style={{ '--accent': accent || '#6366f1' }}>
      <div className="stat-card-inner">
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
        </div>
        <div className="stat-icon" style={{ background: BG[colorKey] || BG.blue }}>
          {ICONS[colorKey] || ICONS.blue}
        </div>
      </div>
    </div>
  )
}
