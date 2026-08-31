import { useEffect, useState } from 'react'
import api from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'

export default function KnowledgeBase() {
  const [articles, setArticles] = useState([])

  useEffect(() => {
    api.get('/knowledge-base').then((r) => setArticles(r.data))
  }, [])

  if (!articles.length) return <LoadingSpinner message="Loading knowledge base..." />

  return (
    <div>
      <PageHeader title="Knowledge Base" subtitle="Self-service guides and troubleshooting articles" />
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
        {articles.map((a) => (
          <div key={a.id} className="card" style={{ cursor: 'default' }}>
            <span className="badge" style={{ background: 'var(--ai-soft)', color: 'var(--ai)', border: '1px solid rgba(139,92,246,0.25)', marginBottom: '0.75rem' }}>
              {a.category}
            </span>
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1rem', fontWeight: 700 }}>{a.title}</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: 0, lineHeight: 1.6 }}>
              {a.content.slice(0, 140)}...
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
