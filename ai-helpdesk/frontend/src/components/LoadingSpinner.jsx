export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="loading-screen">
      <div className="spinner" />
      <span>{message}</span>
    </div>
  )
}
