import { IconSparkle } from './Icons'

export default function AIBlock({ title, children }) {
  return (
    <div className="ai-block">
      <div className="ai-label"><IconSparkle /> {title}</div>
      <div style={{ marginTop: '0.875rem', fontSize: '0.9375rem', lineHeight: 1.6 }}>{children}</div>
    </div>
  )
}
