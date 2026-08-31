import { useEffect, useState } from 'react'
import api from '../services/api'
import TicketTable from '../components/TicketTable'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Suppressed() {
  const [tickets, setTickets] = useState(null)

  useEffect(() => {
    api.get('/tickets/suppressed').then((r) => setTickets(r.data))
  }, [])

  if (tickets === null) return <LoadingSpinner message="Loading suppressed requests..." />

  return (
    <div>
      <PageHeader title="Suppressed Requests" subtitle="Issues rejected or handled via self-service by AI" />
      {tickets.length ? <TicketTable tickets={tickets} /> : <div className="card empty">No suppressed requests</div>}
    </div>
  )
}
