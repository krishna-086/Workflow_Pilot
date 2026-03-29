import { useState, useEffect, useRef, useCallback } from 'react'

export function useWorkflow() {
  const [workflows, setWorkflows] = useState({})
  const [workflowIds, setWorkflowIds] = useState({})
  const [auditEntries, setAuditEntries] = useState([])
  const [auditSummary, setAuditSummary] = useState({})
  const [isRunning, setIsRunning] = useState(false)
  const [startTime, setStartTime] = useState(null)
  const [elapsed, setElapsed] = useState(0)

  // Polling for workflow status and audit trail
  useEffect(() => {
    if (!isRunning && Object.keys(workflowIds).length === 0) return

    const pollInterval = setInterval(async () => {
      try {
        // Fetch audit trail
        const auditRes = await fetch('/api/audit')
        if (auditRes.ok) {
          const auditData = await auditRes.json()
          setAuditEntries(auditData.entries || [])
          setAuditSummary(auditData.summary || {})
        }

        // Fetch individual workflow status
        for (const [scenario, id] of Object.entries(workflowIds)) {
          if (id) {
            const wfRes = await fetch(`/api/workflow/${id}`)
            if (wfRes.ok) {
              const wfData = await wfRes.json()
              setWorkflows(prev => ({ ...prev, [scenario]: wfData }))
            }
          }
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 1500)

    return () => clearInterval(pollInterval)
  }, [isRunning, workflowIds])

  // Check if all workflows completed
  useEffect(() => {
    const wfValues = Object.values(workflows)
    if (wfValues.length > 0 && wfValues.every(w => w?.status === 'completed' || w?.status === 'failed')) {
      setIsRunning(false)
    }
  }, [workflows])

  // Elapsed time counter
  useEffect(() => {
    if (!startTime || !isRunning) return

    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime, isRunning])

  // Run all scenarios
  const runAll = useCallback(async () => {
    try {
      // Reset first
      await fetch('/api/reset', { method: 'POST' })
      setWorkflows({})
      setAuditEntries([])
      setAuditSummary({})

      setIsRunning(true)
      setStartTime(Date.now())
      setElapsed(0)

      const res = await fetch('/api/demo/run-all', { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setWorkflowIds(data.workflow_ids)
        setWorkflows({
          onboarding: { status: 'starting' },
          meeting: { status: 'starting' },
          sla: { status: 'starting' }
        })
      }
    } catch (error) {
      console.error('Failed to start workflows:', error)
      setIsRunning(false)
    }
  }, [])

  // Run a single scenario
  const runScenario = useCallback(async (scenario, data) => {
    try {
      // Reset first
      await fetch('/api/reset', { method: 'POST' })
      setWorkflows({})
      setAuditEntries([])
      setAuditSummary({})
      setWorkflowIds({})

      setIsRunning(true)
      setStartTime(Date.now())
      setElapsed(0)

      let endpoint = ''
      let body = {}

      if (scenario === 'onboarding') {
        endpoint = '/api/workflow/onboarding'
        body = data
      } else if (scenario === 'meeting') {
        endpoint = '/api/workflow/meeting'
        body = {
          transcript: data.transcript,
          participants: data.participants
        }
      } else if (scenario === 'sla') {
        endpoint = '/api/workflow/sla'
        body = data
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (res.ok) {
        const result = await res.json()
        setWorkflowIds({ [scenario]: result.workflow_id })
        setWorkflows({ [scenario]: { status: 'starting' } })
      }
    } catch (error) {
      console.error('Failed to start scenario:', error)
      setIsRunning(false)
    }
  }, [])

  // Reset system
  const reset = useCallback(async () => {
    try {
      await fetch('/api/reset', { method: 'POST' })
      setWorkflows({})
      setWorkflowIds({})
      setAuditEntries([])
      setAuditSummary({})
      setIsRunning(false)
      setStartTime(null)
      setElapsed(0)
    } catch (error) {
      console.error('Failed to reset:', error)
    }
  }, [])

  // Helper: get entries for a specific scenario
  const getScenarioEntries = useCallback((scenario) => {
    return auditEntries.filter(e => e.scenario === scenario)
  }, [auditEntries])

  // Helper: map step keys to their audit entries
  const getEntryMap = useCallback((scenario) => {
    const entries = getScenarioEntries(scenario)
    const map = {}

    entries.forEach(entry => {
      const key = mapActionToKey(entry.action)
      if (key) {
        map[key] = entry
      }
    })

    return map
  }, [getScenarioEntries])

  // Helper: get completed step keys
  const getCompletedKeys = useCallback((scenario) => {
    const entries = getScenarioEntries(scenario)
    const completed = new Set()

    entries.forEach(entry => {
      const key = mapActionToKey(entry.action)
      if (key) {
        completed.add(key)
      }
    })

    return completed
  }, [getScenarioEntries])

  // Helper: get error step keys
  const getErrorKeys = useCallback((scenario) => {
    const entries = getScenarioEntries(scenario)
    const errors = new Set()

    entries.forEach(entry => {
      const key = mapActionToKey(entry.action)
      if (key && entry.status === 'failure') {
        errors.add(key)
      }
    })

    return errors
  }, [getScenarioEntries])

  // Helper: get current active step key
  const getActiveKey = useCallback((scenario, stepDefs) => {
    const completed = getCompletedKeys(scenario)
    const status = workflows[scenario]?.status

    if (!['running', 'starting', 'in_progress'].includes(status)) {
      return null
    }

    for (const step of stepDefs) {
      if (!completed.has(step.key)) {
        return step.key
      }
    }

    return null
  }, [getCompletedKeys, workflows])

  return {
    workflows,
    workflowIds,
    auditEntries,
    auditSummary,
    isRunning,
    elapsed,
    runAll,
    runScenario,
    reset,
    getScenarioEntries,
    getEntryMap,
    getCompletedKeys,
    getErrorKeys,
    getActiveKey
  }
}

// Map audit action to step key
function mapActionToKey(action) {
  if (!action) return null
  const a = action.toLowerCase()

  if (a.includes('classify')) return 'classify'
  if (a.includes('ad_account') || a.includes('active_dir')) return 'ad'
  if (a.includes('jira') && (a.includes('retry') || a.includes('recovery') || a.includes('analy'))) return 'retry'
  if (a.includes('jira')) return 'jira'
  if (a.includes('escalat')) return 'escalate'
  if (a.includes('email_account') || a.includes('google_work') || a.includes('create_email')) return 'email'
  if (a.includes('buddy')) return 'buddy'
  if (a.includes('orient')) return 'orient'
  if (a.includes('welcome')) return 'welcome'
  if (a.includes('finalize') || a.includes('run_onboard') || a.includes('run_meet') || a.includes('run_sla')) return 'final'
  if (a.includes('extract') || a.includes('action_item')) return 'extract'
  if (a.includes('owner') || a.includes('identify')) return 'owners'
  if (a.includes('human')) return 'human'
  if (a.includes('task') && a.includes('creat')) return 'tasks'
  if (a.includes('summary') || a.includes('send_meet')) return 'summary'
  if (a.includes('detect') || a.includes('breach')) return 'detect'
  if (a.includes('bottleneck')) return 'bottleneck'
  if (a.includes('delegat')) return 'delegate'
  if (a.includes('reroute')) return 'reroute'
  if (a.includes('compliance')) return 'compliance'

  return null
}
