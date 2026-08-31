import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Layout from '../layouts/Layout'

export default function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="container" style={{ padding: '3rem' }}>Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />
  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}
