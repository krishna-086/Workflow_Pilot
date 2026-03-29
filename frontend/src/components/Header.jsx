function Header({ onRunAll, onReset, isRunning, elapsed }) {
  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <header className="header">
      <div className="header-left">
        <div className="logo">
          <svg viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5">
            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div className="header-title">
          <h1>WorkflowPilot</h1>
          <div className="sub">Autonomous Enterprise Workflows • ET AI Hackathon 2026</div>
        </div>
      </div>

      <div className="header-right">
        <button className="btn btn-ghost" onClick={onReset}>
          Reset
        </button>
        <button
          className="btn btn-primary"
          onClick={onRunAll}
          disabled={isRunning}
        >
          {isRunning ? `RUNNING ${formatTime(elapsed)}` : '▶  RUN ALL SCENARIOS'}
        </button>
      </div>
    </header>
  )
}

export default Header
