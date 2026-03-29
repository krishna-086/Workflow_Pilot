import { useState } from 'react'

function HumanInputModal({ onSubmit, onClose }) {
  const [assignee, setAssignee] = useState('Rahul Mehta')

  const participants = [
    { name: 'Rahul Mehta', note: 'Eng Manager — most relevant' },
    { name: 'Vikram Patel', note: 'Design Lead' },
    { name: 'Ananya Desai', note: 'Product Manager' },
    { name: 'Neha Gupta', note: 'QA Lead' },
  ]

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <h3>
          <span className="blink">🙋</span>
          Human Input Required
        </h3>

        <p>
          The AI agent found an action item with <strong>no clear owner</strong>.
          As per policy, the system does not guess — it asks a human operator.
        </p>

        <div className="modal-flag">
          <div className="flag-title">
            📌 "Write API documentation for new dashboard endpoints"
          </div>
          <div className="flag-conf">
            Owner confidence: 0.0 — No participant volunteered
          </div>
          <div className="flag-reason">
            Vikram mentioned he's "swamped", Rahul deflected. No one committed to this item in the meeting.
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Assign to:</label>
          <select
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
          >
            {participants.map(p => (
              <option key={p.name} value={p.name}>
                {p.name} ({p.note})
              </option>
            ))}
          </select>
        </div>

        <div className="modal-actions">
          <button className="btn btn-amber" onClick={onSubmit}>
            ✓ Assign & Continue Workflow
          </button>
        </div>
      </div>
    </div>
  )
}

export default HumanInputModal
