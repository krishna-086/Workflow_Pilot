import { STEP_DEFINITIONS } from '../utils/stepDefinitions'
import { mapActionToKey } from '../utils/auditMapper'

function PipelinePanel({ activeTab, auditEntries, workflows }) {
  const steps = STEP_DEFINITIONS[activeTab] || []
  const scenarioEntries = auditEntries.filter(e => e.scenario === activeTab)

  // Build entry map and sets
  const entryMap = {}
  const completedKeys = new Set()
  const errorKeys = new Set()

  scenarioEntries.forEach(entry => {
    const key = mapActionToKey(entry.action)
    if (key) {
      entryMap[key] = entry
      completedKeys.add(key)
      if (entry.status === 'failure') {
        errorKeys.add(key)
      }
    }
  })

  // Determine active key
  const status = workflows[activeTab]?.status
  const isRunning = ['running', 'starting', 'in_progress'].includes(status)

  let activeKey = null
  if (isRunning) {
    for (const step of steps) {
      if (!completedKeys.has(step.key)) {
        activeKey = step.key
        break
      }
    }
  }

  // Get step state
  const getStepState = (step) => {
    if (activeKey === step.key) {
      return step.isHuman ? 'human' : 'active'
    }
    if (errorKeys.has(step.key)) {
      return 'error'
    }
    if (completedKeys.has(step.key)) {
      if (step.isRetry) return 'retry'
      if (step.isEscalate) return 'escalated'
      if (step.isHuman) return 'completed'
      return 'completed'
    }
    return 'pending'
  }

  // Get model display
  const getModelDisplay = (entry) => {
    if (!entry?.model_used || entry.model_used === 'none') return null
    if (entry.model_used.includes('llama')) return 'llama-70b'
    if (entry.model_used.includes('gemini')) return 'gemini'
    return 'LLM'
  }

  return (
    <div className="panel panel-center">
      <div className="panel-title">Agent Pipeline</div>

      {steps.map(step => {
        const state = getStepState(step)
        const entry = entryMap[step.key]
        const model = getModelDisplay(entry)
        const reasoning = entry?.decision_reasoning

        return (
          <div key={step.key} className={`step ${state}`}>
            <div className="step-icon">{step.icon}</div>

            <div className="step-body">
              <div className="step-header">
                <span className="step-name">{step.label}</span>
                <span className="step-agent">{step.agent}</span>
                {model && <span className="step-model mono">{model}</span>}
              </div>

              {state !== 'pending' && reasoning && (
                <div className="step-detail">
                  💭 {reasoning.length > 200 ? reasoning.slice(0, 200) + '...' : reasoning}
                </div>
              )}

              {state === 'error' && (
                <div className="step-detail error">
                  ❌ JIRA API Error 403: License seat limit reached
                </div>
              )}

              {state === 'escalated' && (
                <div className="step-detail escalated">
                  🚨 Escalated to #it-helpdesk
                  {reasoning && `\n${reasoning.slice(0, 150)}`}
                </div>
              )}

              {state === 'human' && (
                <div className="step-detail human">
                  ⏳ Ambiguous owner detected — waiting for human decision...
                </div>
              )}

              {step.isHuman && state === 'completed' && (
                <div className="step-detail human">
                  👤 Human operator assigned owner
                </div>
              )}
            </div>

            <StepStatusIcon state={state} />
          </div>
        )
      })}
    </div>
  )
}

function StepStatusIcon({ state }) {
  switch (state) {
    case 'active':
      return <div className="spinner" />
    case 'completed':
      return <span className="step-status success">✓</span>
    case 'error':
      return <span className="step-status error">✗</span>
    case 'human':
      return <span className="step-status amber blink">⏳</span>
    case 'escalated':
      return <span className="step-status error">⬆</span>
    case 'retry':
      return <span className="step-status amber">↻</span>
    default:
      return <span className="step-status muted">—</span>
  }
}

export default PipelinePanel
