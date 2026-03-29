// Map audit action to step key
export function mapActionToKey(action) {
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

// Build entry map from audit entries
export function buildEntryMap(entries) {
  const map = {}
  entries.forEach(entry => {
    const key = mapActionToKey(entry.action)
    if (key) {
      map[key] = entry
    }
  })
  return map
}

// Get completed keys
export function getCompletedKeys(entries) {
  const completed = new Set()
  entries.forEach(entry => {
    const key = mapActionToKey(entry.action)
    if (key) {
      completed.add(key)
    }
  })
  return completed
}

// Get error keys
export function getErrorKeys(entries) {
  const errors = new Set()
  entries.forEach(entry => {
    const key = mapActionToKey(entry.action)
    if (key && entry.status === 'failure') {
      errors.add(key)
    }
  })
  return errors
}
