import { useState, useEffect } from 'react'
import Header from './components/Header'
import MetricsBar from './components/MetricsBar'
import ScenarioTabs from './components/ScenarioTabs'
import InputPanel from './components/InputPanel'
import PipelinePanel from './components/PipelinePanel'
import OutputPanel from './components/OutputPanel'
import HumanInputModal from './components/HumanInputModal'
import { useWorkflow } from './hooks/useWorkflow'
import { DEFAULT_TRANSCRIPT } from './data/defaultTranscript'

function App() {
  const [activeTab, setActiveTab] = useState('onboarding')
  const [showHumanModal, setShowHumanModal] = useState(false)
  const [humanModalDone, setHumanModalDone] = useState(false)

  // Form states
  const [onboardingForm, setOnboardingForm] = useState({
    employee_name: 'Priya Sharma',
    email: 'priya.sharma@company.com',
    role: 'Senior Frontend Developer',
    department: 'Engineering',
    manager: 'Rahul Mehta',
    start_date: '2026-03-30'
  })

  const [meetingForm, setMeetingForm] = useState({
    transcript: DEFAULT_TRANSCRIPT,
    participants: ['Rahul Mehta', 'Ananya Desai', 'Vikram Patel', 'Neha Gupta']
  })

  const [slaForm, setSlaForm] = useState({
    request_id: 'PROC-2026-0847',
    type: 'procurement',
    requested_by: 'Amit Verma',
    approver: 'David Kim',
    submitted_at: '2026-03-27T09:00:00Z',
    sla_deadline: '2026-03-29T09:00:00Z'
  })

  const workflow = useWorkflow()

  // Auto-switch tabs when workflows are running
  useEffect(() => {
    if (!workflow.isRunning) return

    const { workflows } = workflow
    if (workflows.sla?.status === 'running') {
      setActiveTab('sla')
    } else if (workflows.meeting?.status === 'running') {
      setActiveTab('meeting')
    } else if (workflows.onboarding?.status === 'running') {
      setActiveTab('onboarding')
    }
  }, [workflow.isRunning, workflow.workflows])

  // Detect human input needed for meeting scenario
  useEffect(() => {
    if (humanModalDone) return

    const meetingEntries = workflow.getScenarioEntries('meeting')
    const hasOwners = meetingEntries.some(e =>
      e.action?.toLowerCase().includes('owner') || e.action?.toLowerCase().includes('identify')
    )
    const hasHuman = meetingEntries.some(e =>
      e.action?.toLowerCase().includes('human')
    )

    if (hasOwners && !hasHuman && workflow.workflows.meeting?.status === 'running') {
      setShowHumanModal(true)
    }

    if (hasHuman) {
      setShowHumanModal(false)
      setHumanModalDone(true)
    }
  }, [workflow.auditEntries, workflow.workflows.meeting, humanModalDone])

  const handleRunScenario = async (scenario) => {
    if (scenario === 'onboarding') {
      await workflow.runScenario('onboarding', onboardingForm)
    } else if (scenario === 'meeting') {
      await workflow.runScenario('meeting', meetingForm)
    } else if (scenario === 'sla') {
      await workflow.runScenario('sla', slaForm)
    }
    setActiveTab(scenario)
  }

  const handleReset = async () => {
    await workflow.reset()
    setHumanModalDone(false)
    setShowHumanModal(false)
  }

  const handleHumanSubmit = () => {
    setShowHumanModal(false)
    setHumanModalDone(true)
  }

  return (
    <div className="app">
      <Header
        onRunAll={workflow.runAll}
        onReset={handleReset}
        isRunning={workflow.isRunning}
        elapsed={workflow.elapsed}
      />
      <MetricsBar summary={workflow.auditSummary} elapsed={workflow.elapsed} />
      <ScenarioTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        workflows={workflow.workflows}
      />

      <div className="main-content">
        <InputPanel
          activeTab={activeTab}
          onboardingForm={onboardingForm}
          setOnboardingForm={setOnboardingForm}
          meetingForm={meetingForm}
          setMeetingForm={setMeetingForm}
          slaForm={slaForm}
          setSlaForm={setSlaForm}
          onRunScenario={handleRunScenario}
          isRunning={workflow.isRunning}
        />
        <PipelinePanel
          activeTab={activeTab}
          auditEntries={workflow.auditEntries}
          workflows={workflow.workflows}
        />
        <OutputPanel
          activeTab={activeTab}
          auditEntries={workflow.auditEntries}
          workflows={workflow.workflows}
          formData={{
            onboarding: onboardingForm,
            meeting: meetingForm,
            sla: slaForm
          }}
        />
      </div>

      {showHumanModal && (
        <HumanInputModal
          onSubmit={handleHumanSubmit}
          onClose={() => setShowHumanModal(false)}
        />
      )}
    </div>
  )
}

export default App
