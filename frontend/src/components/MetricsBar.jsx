function MetricsBar({ summary, elapsed }) {
  const totalActions = summary.total_actions || 0
  const llmCalls = Object.entries(summary.models_used || {})
    .filter(([k]) => k !== 'none')
    .reduce((sum, [, v]) => sum + v, 0)
  const errorCount = summary.error_count || 0
  const totalTokens = summary.total_tokens || 0

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="metrics-bar">
      <div className="metric">
        <span className="metric-icon">⚡</span>
        <div>
          <div className="metric-value">{totalActions}</div>
          <div className="metric-label">Actions</div>
        </div>
      </div>

      <div className="metric">
        <span className="metric-icon">🧠</span>
        <div>
          <div className="metric-value">{llmCalls}</div>
          <div className="metric-label">LLM Calls</div>
        </div>
      </div>

      <div className="metric">
        <span className="metric-icon">🛡️</span>
        <div>
          <div className="metric-value">{errorCount}</div>
          <div className="metric-label">Errors</div>
        </div>
      </div>

      <div className="metric">
        <span className="metric-icon">📊</span>
        <div>
          <div className="metric-value">{totalTokens.toLocaleString()}</div>
          <div className="metric-label">Tokens</div>
        </div>
      </div>

      <div className="metric">
        <span className="metric-icon">⏱</span>
        <div>
          <div className="metric-value">{formatTime(elapsed)}</div>
          <div className="metric-label">Time</div>
        </div>
      </div>
    </div>
  )
}

export default MetricsBar
