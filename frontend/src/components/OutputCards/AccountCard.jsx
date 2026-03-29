import { useState } from 'react'

function AccountCard({ icon, title, name, detail, status, headerClass }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const text = `${title}\nName: ${name}\nDetails: ${detail}\nStatus: ${status}`
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const iconClass = title.toLowerCase().includes('jira') ? 'jira'
    : title.toLowerCase().includes('email') ? 'email'
    : 'ad'

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
        <div className="account-card">
          <div className={`account-icon ${iconClass}`}>
            {icon}
          </div>
          <div className="account-info">
            <div className="account-name">{name}</div>
            <div className="account-detail">{detail}</div>
          </div>
          <span className={`account-status ${status === 'success' ? 'success' : 'failed'}`}>
            {status === 'success' ? '✓ Created' : '✗ Failed'}
          </span>
        </div>
      </div>
    </div>
  )
}

export default AccountCard
