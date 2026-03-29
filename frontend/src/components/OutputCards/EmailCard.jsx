import { useState } from 'react'

function EmailCard({ icon, title, from, to, subject, body, headerClass }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const text = `From: ${from}\nTo: ${to}\nSubject: ${subject}\n\n${body}`
    await navigator.clipboard.writeText(text)
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
        <div className="email-card">
          <div className="email-field">
            <span className="email-key">From</span>
            <span className="email-val">{from}</span>
          </div>
          <div className="email-field">
            <span className="email-key">To</span>
            <span className="email-val">{to}</span>
          </div>
          <div className="email-field">
            <span className="email-key">Subject</span>
            <span className="email-val subject">{subject}</span>
          </div>
          <div className="email-body">{body}</div>
        </div>
      </div>
    </div>
  )
}

export default EmailCard
