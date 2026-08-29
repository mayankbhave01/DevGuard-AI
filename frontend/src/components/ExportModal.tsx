import { useState } from 'react'
import {
  Archive,
  Braces,
  Code2,
  Download,
  FileSpreadsheet,
  FileText,
  FileType2,
  X,
} from 'lucide-react'
import { API_URL } from '../api/client'

const formats = [
  { id: 'pdf', label: 'PDF', note: 'Polished shareable report', icon: FileType2, ext: 'pdf' },
  { id: 'html', label: 'HTML', note: 'Standalone browser report', icon: Code2, ext: 'html' },
  { id: 'md', label: 'Markdown', note: 'GitHub and documentation', icon: FileText, ext: 'md' },
  { id: 'json', label: 'JSON', note: 'API and automation', icon: Braces, ext: 'json' },
  { id: 'csv', label: 'CSV', note: 'Excel and analysis', icon: FileSpreadsheet, ext: 'csv' },
  { id: 'txt', label: 'Text', note: 'Simple portable report', icon: FileText, ext: 'txt' },
  { id: 'zip', label: 'All formats', note: 'PDF + HTML + MD + JSON + CSV + TXT', icon: Archive, ext: 'zip', featured: true },
]

type Props = { scanId: number; title: string; onClose: () => void }

export default function ExportModal({ scanId, title, onClose }: Props) {
  const [mode, setMode] = useState<'summary' | 'detailed'>('detailed')
  const [source, setSource] = useState(true)
  const [suggestions, setSuggestions] = useState(true)
  const [summary, setSummary] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const download = async (format: string, ext: string) => {
    setBusy(format); setError('')
    try {
      const token = localStorage.getItem('devguard_token')
      const q = new URLSearchParams({
        include_source: String(source),
        include_suggestions: String(suggestions),
        include_summary: String(summary),
        mode,
      })
      const r = await fetch(`${API_URL}/api/scans/${scanId}/export/${format}?${q}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail || 'Export failed')
      const blob = await r.blob()
      const cd = r.headers.get('content-disposition') || ''
      const serverName = cd.match(/filename="?([^";]+)"?/i)?.[1]
      const safeTitle = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || `scan-${scanId}`
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = serverName || `devguard-${safeTitle}.${ext}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(a.href)
    } catch (e: any) {
      setError(e.message || 'Export failed')
    } finally { setBusy('') }
  }

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="export-modal" onMouseDown={e => e.stopPropagation()}>
        <div className="modal-head">
          <div><p className="eyebrow">Flexible reporting</p><h2>Download report</h2><p>Choose the format and exactly what the report should include.</p></div>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={20}/></button>
        </div>

        <div className="export-settings">
          <label><span>Report depth</span><select value={mode} onChange={e => setMode(e.target.value as 'summary'|'detailed')}><option value="detailed">Detailed — full findings</option><option value="summary">Summary — compact overview</option></select></label>
          <div className="option-pills">
            <label className="check-pill"><input type="checkbox" checked={source} onChange={e=>setSource(e.target.checked)}/><span>Include source code</span></label>
            <label className="check-pill"><input type="checkbox" checked={suggestions} onChange={e=>setSuggestions(e.target.checked)}/><span>Include suggested fixes</span></label>
            <label className="check-pill"><input type="checkbox" checked={summary} onChange={e=>setSummary(e.target.checked)}/><span>Include AI summary</span></label>
          </div>
        </div>

        <div className="format-grid">
          {formats.map(f => {
            const Icon = f.icon
            return <button key={f.id} className={`format-card ${f.featured ? 'featured' : ''}`} onClick={()=>download(f.id,f.ext)} disabled={!!busy}>
              <span className="format-icon"><Icon size={21}/></span>
              <span><b>{busy===f.id ? 'Preparing…' : f.label}</b><small>{f.note}</small></span>
              <Download size={17}/>
            </button>
          })}
        </div>
        {error && <div className="error-box">{error}</div>}
        <div className="modal-foot"><span>Tip: <b>All formats</b> downloads one ZIP containing every report format.</span></div>
      </div>
    </div>
  )
}
