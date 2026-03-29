import { useState } from 'react'

function ComplianceCard({ icon, title, content, headerClass }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

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
        <div className="text-content" style={{ whiteSpace: 'pre-wrap' }}>
          {content}
        </div>
      </div>
    </div>
  )
}

export default ComplianceCard
