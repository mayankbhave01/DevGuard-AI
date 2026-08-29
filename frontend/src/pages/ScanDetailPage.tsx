import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { useParams } from 'react-router-dom'
import { AlertTriangle, Download, ShieldCheck, Sparkles, TerminalSquare } from 'lucide-react'
import { api } from '../api/client'
import type { Scan } from '../types'
import SeverityBadge from '../components/SeverityBadge'
import ExportModal from '../components/ExportModal'

export default function ScanDetailPage(){
  const { id } = useParams()
  const [scan,setScan]=useState<Scan|null>(null)
  const [filter,setFilter]=useState('all')
  const [exportOpen,setExportOpen]=useState(false)
  const [error,setError]=useState('')
  useEffect(()=>{api.get(`/scans/${id}`).then(r=>setScan(r.data)).catch(e=>setError(e.response?.data?.detail||'Could not load scan.'))},[id])
  const issues=useMemo(()=>scan?.issues?.filter(i=>filter==='all'||i.severity===filter)||[],[scan,filter])
  if(error)return <div className="error-box">{error}</div>
  if(!scan)return <div className="loading">Loading scan…</div>
  const riskLabel = scan.score >= 80 ? 'Healthy' : scan.score >= 60 ? 'Needs attention' : 'High risk'
  return <>
    <div className="scan-hero">
      <div className="scan-hero-copy"><p className="eyebrow">Scan #{scan.id} • {scan.language}</p><h1>{scan.title}</h1><p>{new Date(scan.created_at).toLocaleString()} • Deterministic security + quality review</p><div className="hero-tags"><span><ShieldCheck size={14}/> {riskLabel}</span><span><TerminalSquare size={14}/> {scan.issue_count} findings</span></div></div>
      <div className="hero-score" style={{'--score': `${scan.score * 3.6}deg`} as CSSProperties}><div><strong>{scan.score}</strong><span>/100</span></div></div>
      <button className="primary export-trigger" onClick={()=>setExportOpen(true)}><Download size={18}/> Download report</button>
    </div>

    <div className="metric-grid scan-metrics">
      <div className="metric"><div className="metric-icon"><ShieldCheck/></div><div><span>Code health score</span><strong>{scan.score}/100</strong><small>{riskLabel}</small></div></div>
      <div className="metric"><div className="metric-icon"><AlertTriangle/></div><div><span>Total issues</span><strong>{scan.issue_count}</strong><small>Across all severities</small></div></div>
      <div className="metric danger-metric"><div><span>Critical</span><strong>{scan.critical_count}</strong><small>Immediate attention</small></div></div>
      <div className="metric warning-metric"><div><span>High</span><strong>{scan.high_count}</strong><small>Prioritize next</small></div></div>
    </div>

    {scan.llm_summary&&<section className="panel ai-panel"><div className="section-kicker"><Sparkles size={17}/> AI deep-review summary</div><pre className="summary-pre">{scan.llm_summary}</pre></section>}

    <section className="panel findings-panel"><div className="section-title"><div><p className="panel-kicker">Security findings</p><h2>Findings</h2></div><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></div><div className="issues">{issues.map(i=><article className={`issue issue-${i.severity}`} key={i.id}><div className="issue-head"><SeverityBadge severity={i.severity}/><code>{i.rule_id}</code><span>{i.category}</span>{i.line&&<span>Line {i.line}</span>}</div><h3>{i.title}</h3><p>{i.description}</p>{i.snippet&&<pre>{i.snippet}</pre>}<div className="suggestion"><b>Suggested fix</b><p>{i.suggestion}</p></div></article>)}{!issues.length&&<div className="empty">No findings in this filter.</div>}</div></section>
    <section className="panel source-panel"><div className="section-title"><div><p className="panel-kicker">Evidence</p><h2>Reviewed source</h2></div><span className="source-language">{scan.language}</span></div><pre className="code-view">{scan.code}</pre></section>
    {exportOpen && <ExportModal scanId={scan.id} title={scan.title} onClose={()=>setExportOpen(false)}/>} 
  </>
}
