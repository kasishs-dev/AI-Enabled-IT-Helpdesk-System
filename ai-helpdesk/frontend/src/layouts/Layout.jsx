import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../services/api'
import {
  IconDashboard, IconTicket, IconReport, IconBell, IconBook,
  IconTeam, IconAudit, IconShield, IconLogout, IconMenu,
} from '../components/Icons'
import './Layout.css'

const NAV = {
  USER: [
    { to: '/dashboard', label: 'Dashboard', icon: IconDashboard },
    { to: '/report', label: 'Report Problem', icon: IconReport },
    { to: '/tickets', label: 'My Tickets', icon: IconTicket },
    { to: '/notifications', label: 'Notifications', icon: IconBell, badge: true },
  ],
  IT_SUPPORT: [
    { to: '/dashboard', label: 'Dashboard', icon: IconDashboard },
    { to: '/tickets', label: 'My Tickets', icon: IconTicket },
    { to: '/knowledge-base', label: 'Knowledge Base', icon: IconBook },
    { to: '/notifications', label: 'Notifications', icon: IconBell, badge: true },
  ],
  IT_MANAGER: [
    { to: '/dashboard', label: 'Dashboard', icon: IconDashboard },
    { to: '/tickets', label: 'All Tickets', icon: IconTicket },
    { to: '/team', label: 'Team', icon: IconTeam },
    { to: '/suppressed', label: 'Suppressed', icon: IconShield },
    { to: '/audit-logs', label: 'Audit Logs', icon: IconAudit },
    { to: '/knowledge-base', label: 'Knowledge Base', icon: IconBook },
    { to: '/notifications', label: 'Notifications', icon: IconBell, badge: true },
  ],
}

const ROLE_LABEL = {
  USER: 'Employee',
  IT_SUPPORT: 'IT Support',
  IT_MANAGER: 'IT Manager',
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [unread, setUnread] = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (!user) return
    api.get('/notifications', { params: { unread_only: true } })
      .then((r) => setUnread(r.data.filter((n) => !n.is_read).length))
      .catch(() => {})
  }, [user, location.pathname])

  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  const links = NAV[user?.role] || []
  const initials = user?.name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()

  return (
    <div className="layout">
      <div className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} onClick={() => setSidebarOpen(false)} />

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand" onClick={() => navigate('/dashboard')}>
          <div className="sidebar-logo">AI</div>
          <div>
            <div className="sidebar-brand-text">Helpdesk</div>
            <div className="sidebar-brand-sub">IT Service Management</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Menu</div>
          {links.map((l) => {
            const Icon = l.icon
            return (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon />
                {l.label}
                {l.badge && unread > 0 && <span className="notif-badge">{unread}</span>}
              </NavLink>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar avatar-sm">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.name}</div>
              <div className="sidebar-user-role">{ROLE_LABEL[user?.role] || user?.role}</div>
            </div>
            <button className="btn btn-ghost btn-icon" onClick={() => { logout(); navigate('/login') }} title="Logout">
              <IconLogout />
            </button>
          </div>
        </div>
      </aside>

      <div className="layout-main">
        <header className="topbar">
          <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
            <IconMenu />
          </button>
          <span className="topbar-title">{ROLE_LABEL[user?.role]} Portal</span>
          <div className="topbar-actions">
            <button className="btn btn-ghost btn-icon" onClick={() => navigate('/notifications')} title="Notifications">
              <IconBell />
              {unread > 0 && <span className="notif-badge" style={{ position: 'absolute', marginTop: '-20px', marginLeft: '16px' }}>{unread}</span>}
            </button>
          </div>
        </header>
        <main className="main page">{children}</main>
      </div>
    </div>
  )
}
