function ScenarioTabs({ activeTab, onTabChange, workflows }) {
  const tabs = [
    { id: 'onboarding', label: '👤 Onboarding' },
    { id: 'meeting', label: '📋 Meeting → Action' },
    { id: 'sla', label: '⏰ SLA Prevention' },
  ]

  const getTabBadge = (scenario) => {
    const status = workflows[scenario]?.status

    if (status === 'completed') {
      return { label: '✓ Done', className: 'completed' }
    }
    if (['running', 'starting', 'in_progress'].includes(status)) {
      return { label: '● Live', className: 'running' }
    }
    if (status === 'failed') {
      return { label: '✗ Failed', className: 'failed' }
    }
    return { label: 'Ready', className: 'ready' }
  }

  return (
    <div className="tabs">
      {tabs.map(tab => {
        const badge = getTabBadge(tab.id)
        return (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
            <span className={`tab-badge ${badge.className}`}>
              {badge.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

export default ScenarioTabs
