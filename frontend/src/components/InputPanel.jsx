function InputPanel({
  activeTab,
  onboardingForm,
  setOnboardingForm,
  meetingForm,
  setMeetingForm,
  slaForm,
  setSlaForm,
  onRunScenario,
  isRunning
}) {
  const wordCount = meetingForm.transcript.split(/\s+/).filter(w => w).length

  return (
    <div className="panel panel-left">
      <div className="panel-title">Input Data</div>

      {activeTab === 'onboarding' && (
        <>
          <div className="form-group">
            <label className="form-label">Employee Name</label>
            <input
              type="text"
              value={onboardingForm.employee_name}
              onChange={(e) => setOnboardingForm({ ...onboardingForm, employee_name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              value={onboardingForm.email}
              onChange={(e) => setOnboardingForm({ ...onboardingForm, email: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Role</label>
            <input
              type="text"
              value={onboardingForm.role}
              onChange={(e) => setOnboardingForm({ ...onboardingForm, role: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Department</label>
            <select
              value={onboardingForm.department}
              onChange={(e) => setOnboardingForm({ ...onboardingForm, department: e.target.value })}
            >
              <option value="Engineering">Engineering</option>
              <option value="Marketing">Marketing</option>
              <option value="Sales">Sales</option>
              <option value="Product">Product</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Manager</label>
            <input
              type="text"
              value={onboardingForm.manager}
              onChange={(e) => setOnboardingForm({ ...onboardingForm, manager: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Start Date</label>
            <input
              type="date"
              value={onboardingForm.start_date}
              onChange={(e) => setOnboardingForm({ ...onboardingForm, start_date: e.target.value })}
            />
          </div>

          <button
            className="btn btn-scenario"
            onClick={() => onRunScenario('onboarding')}
            disabled={isRunning}
          >
            ▶ Run Onboarding
          </button>
        </>
      )}

      {activeTab === 'meeting' && (
        <>
          <div className="form-group">
            <label className="form-label">Meeting Transcript</label>
            <textarea
              rows={16}
              value={meetingForm.transcript}
              onChange={(e) => setMeetingForm({ ...meetingForm, transcript: e.target.value })}
              style={{ fontSize: '11px', lineHeight: 1.6 }}
            />
            <div className="word-count">{wordCount} words</div>
          </div>

          <button
            className="btn btn-scenario"
            onClick={() => onRunScenario('meeting')}
            disabled={isRunning}
          >
            ▶ Run Meeting
          </button>
        </>
      )}

      {activeTab === 'sla' && (
        <>
          <div className="form-group">
            <label className="form-label">Request ID</label>
            <input
              type="text"
              className="mono"
              value={slaForm.request_id}
              onChange={(e) => setSlaForm({ ...slaForm, request_id: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Type</label>
            <select
              value={slaForm.type}
              onChange={(e) => setSlaForm({ ...slaForm, type: e.target.value })}
            >
              <option value="procurement">Procurement</option>
              <option value="travel">Travel</option>
              <option value="software_license">Software License</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Requested By</label>
            <input
              type="text"
              value={slaForm.requested_by}
              onChange={(e) => setSlaForm({ ...slaForm, requested_by: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Approver</label>
            <input
              type="text"
              value={slaForm.approver}
              onChange={(e) => setSlaForm({ ...slaForm, approver: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Stuck Duration</label>
            <input
              type="text"
              value="52 hours"
              readOnly
              className="form-readonly form-error"
            />
          </div>

          <div className="form-group">
            <label className="form-label">SLA Threshold</label>
            <input
              type="text"
              value="24 hours"
              readOnly
              className="form-readonly"
            />
          </div>

          <button
            className="btn btn-scenario"
            onClick={() => onRunScenario('sla')}
            disabled={isRunning}
          >
            ▶ Run SLA
          </button>
        </>
      )}
    </div>
  )
}

export default InputPanel
