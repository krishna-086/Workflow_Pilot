import { useState } from 'react'
import { mapActionToKey } from '../utils/auditMapper'
import EmailCard from './OutputCards/EmailCard'
import AccountCard from './OutputCards/AccountCard'
import ComplianceCard from './OutputCards/ComplianceCard'

function OutputPanel({ activeTab, auditEntries, workflows, formData }) {
  const scenarioEntries = auditEntries.filter(e => e.scenario === activeTab)

  // Build entry map
  const entryMap = {}
  const errorKeys = new Set()

  scenarioEntries.forEach(entry => {
    const key = mapActionToKey(entry.action)
    if (key) {
      entryMap[key] = entry
      if (entry.status === 'failure') {
        errorKeys.add(key)
      }
    }
  })

  const getReasoning = (key) => entryMap[key]?.decision_reasoning || ''
  const hasEntry = (key) => !!entryMap[key]

  const workflow = workflows[activeTab]
  const isStarted = workflow && ['starting', 'running', 'in_progress', 'completed', 'failed'].includes(workflow.status)

  if (!isStarted) {
    return (
      <div className="panel panel-right">
        <div className="panel-title">Generated Output</div>
        <div className="empty-state">
          <p>🎯</p>
          <p>Outputs will appear here as each agent completes its step</p>
        </div>
      </div>
    )
  }

  return (
    <div className="panel panel-right">
      <div className="panel-title">Generated Output</div>

      {activeTab === 'onboarding' && (
        <OnboardingOutputs
          entryMap={entryMap}
          errorKeys={errorKeys}
          getReasoning={getReasoning}
          hasEntry={hasEntry}
          formData={formData.onboarding}
        />
      )}

      {activeTab === 'meeting' && (
        <MeetingOutputs
          entryMap={entryMap}
          getReasoning={getReasoning}
          hasEntry={hasEntry}
        />
      )}

      {activeTab === 'sla' && (
        <SLAOutputs
          entryMap={entryMap}
          getReasoning={getReasoning}
          hasEntry={hasEntry}
          formData={formData.sla}
        />
      )}
    </div>
  )
}

function OnboardingOutputs({ entryMap, errorKeys, getReasoning, hasEntry, formData }) {
  const name = formData.employee_name
  const email = formData.email
  const dept = formData.department
  const role = formData.role

  return (
    <>
      {hasEntry('ad') && (
        <AccountCard
          icon="🔑"
          title="Active Directory Account"
          name={name}
          detail={`${email} • ${dept}`}
          status="success"
        />
      )}

      {errorKeys.has('jira') && (
        <AccountCard
          icon="📋"
          title="JIRA Account — Failed"
          name="JIRA Account"
          detail="Error 403: License seat limit reached"
          status="failed"
          headerClass="error"
        />
      )}

      {hasEntry('escalate') && (
        <EmailCard
          icon="🚨"
          title="IT Escalation Ticket"
          from="WorkflowPilot → #it-helpdesk"
          to="IT Support Team"
          subject={`[URGENT] JIRA provisioning failed for ${name}`}
          body={getReasoning('escalate') || `JIRA account creation for ${name} failed after 3 retry attempts.\n\nError: API 403 — License seat limit reached.\nRequested action: Add JIRA license seat and create account.\nPriority: High — New hire starts ${formData.start_date}.`}
          headerClass="error"
        />
      )}

      {hasEntry('email') && (
        <AccountCard
          icon="📧"
          title="Email Account"
          name={name}
          detail={`${name.toLowerCase().replace(' ', '.')}@company.com`}
          status="success"
        />
      )}

      {hasEntry('buddy') && (
        <TextCard
          icon="🤝"
          title="Buddy Assignment"
          content={getReasoning('buddy') || `Assigned buddy from ${dept} department`}
        />
      )}

      {hasEntry('welcome') && (
        <EmailCard
          icon="🎉"
          title="Welcome Email (AI Generated)"
          from="HR Team"
          to={email}
          subject={`Welcome to the team, ${name.split(' ')[0]}!`}
          body={getReasoning('welcome') || `Dear ${name},\n\nWelcome to ${dept}! We're thrilled to have you join us as ${role}.\n\nYour orientation has been scheduled and your buddy will reach out shortly.\n\nBest regards,\nHR Team`}
          headerClass="success"
        />
      )}
    </>
  )
}

function MeetingOutputs({ entryMap, getReasoning, hasEntry }) {
  return (
    <>
      {hasEntry('extract') && (
        <TextCard
          icon="🔍"
          title="Extracted Action Items"
          content={getReasoning('extract') || 'Analyzing transcript...'}
        />
      )}

      {hasEntry('owners') && (
        <TextCard
          icon="👥"
          title="Owner Assignment Analysis"
          content={getReasoning('owners') || 'Identifying owners...'}
        />
      )}

      {hasEntry('human') && (
        <TextCard
          icon="🙋"
          title="Human Intervention"
          content={getReasoning('human') || 'Human operator assigned the ambiguous action item'}
          headerClass="amber"
        />
      )}

      {hasEntry('tasks') && (
        <TextCard
          icon="📝"
          title="Tasks Created in Tracker"
          content={getReasoning('tasks') || 'Tasks created successfully'}
        />
      )}

      {hasEntry('summary') && (
        <EmailCard
          icon="📤"
          title="Meeting Summary Email (AI Generated)"
          from="WorkflowPilot"
          to="Rahul, Ananya, Vikram, Neha"
          subject="Meeting Follow-up: Dashboard Launch — Action Items"
          body={getReasoning('summary') || 'Summary email content...'}
          headerClass="success"
        />
      )}
    </>
  )
}

function SLAOutputs({ entryMap, getReasoning, hasEntry, formData }) {
  return (
    <>
      {hasEntry('detect') && (
        <TextCard
          icon="⚠️"
          title="SLA Breach Alert"
          content={getReasoning('detect') || 'Detecting breach...'}
          headerClass="error"
        />
      )}

      {hasEntry('bottleneck') && (
        <TextCard
          icon="🔎"
          title="Root Cause Analysis (AI)"
          content={getReasoning('bottleneck') || 'Analyzing...'}
        />
      )}

      {hasEntry('delegate') && (
        <TextCard
          icon="🔗"
          title="Delegate Verification"
          content={getReasoning('delegate') || 'Finding delegate...'}
        />
      )}

      {hasEntry('reroute') && (
        <EmailCard
          icon="↩️"
          title="Approval Rerouted"
          from="WorkflowPilot"
          to="Sarah Chen (Delegate)"
          subject={`[ACTION] Rerouted: ${formData.request_id} — Procurement Approval`}
          body={getReasoning('reroute') || `This procurement approval has been rerouted to you as delegate.\n\nOriginal approver: ${formData.approver} (on leave)\nRequest ID: ${formData.request_id}\nStuck for: 52 hours\nSLA Status: BREACHED\n\nPlease review and approve at your earliest convenience.`}
        />
      )}

      {hasEntry('compliance') && (
        <ComplianceCard
          icon="📜"
          title="Compliance Audit Record"
          content={getReasoning('compliance') || 'Compliance record generated'}
          headerClass="success"
        />
      )}
    </>
  )
}

function TextCard({ icon, title, content, headerClass }) {
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const TRUNCATE_LENGTH = 200
  const isLong = content && content.length > TRUNCATE_LENGTH

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const displayContent = isLong && !expanded
    ? content.slice(0, TRUNCATE_LENGTH) + '...'
    : content

  return (
    <div className="output-card fade-in">
      <div className={`output-card-header ${headerClass || ''}`}>
        <div className="output-card-header-left">
          <span className="oico">{icon}</span>
          {title}
        </div>
        <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy}>
          {copied ? '✓ Copied' : '📋 Copy'}
        </button>
      </div>
      <div className="output-card-body">
        <div className="text-content" style={{ whiteSpace: 'pre-wrap' }}>{displayContent}</div>
        {isLong && (
          <button
            className="expand-btn"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? '▲ Show less' : '▼ Show more'}
          </button>
        )}
      </div>
    </div>
  )
}

export default OutputPanel
