import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import UserDashboard from './pages/UserDashboard'
import ITDashboard from './pages/ITDashboard'
import ManagerDashboard from './pages/ManagerDashboard'
import ReportProblem from './pages/ReportProblem'
import Tickets from './pages/Tickets'
import TicketDetail from './pages/TicketDetail'
import Notifications from './pages/Notifications'
import KnowledgeBase from './pages/KnowledgeBase'
import AuditLogs from './pages/AuditLogs'
import Team from './pages/Team'
import Suppressed from './pages/Suppressed'

function RoleDashboard() {
  const { user } = useAuth()
  if (user?.role === 'IT_MANAGER') return <ManagerDashboard />
  if (user?.role === 'IT_SUPPORT') return <ITDashboard />
  return <UserDashboard />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<RoleDashboard />} />
        <Route path="/tickets" element={<Tickets />} />
        <Route path="/tickets/:id" element={<TicketDetail />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
      </Route>
      <Route element={<ProtectedRoute roles={['USER']} />}>
        <Route path="/report" element={<ReportProblem />} />
      </Route>
      <Route element={<ProtectedRoute roles={['IT_MANAGER']} />}>
        <Route path="/audit-logs" element={<AuditLogs />} />
        <Route path="/team" element={<Team />} />
        <Route path="/suppressed" element={<Suppressed />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
