import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock3, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import type { Scan } from '../types'

export default function HistoryPage() {
  const [scans, setScans] = useState<Scan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = useCallback(async () => { try { setError(''); const response = await api.get('/scans'); setScans(Array.isArray(response.data) ? response.data : []) } catch (err:any) { setError(err?.response?.data?.detail || 'Could not load scan history.') } finally { setLoading(false) } }, [])
  useEffect(() => { void load() }, [load])
  const del = async (id:number) => { if (!confirm('Delete this scan?')) return; try { await api.delete(`/scans/${id}`); await load() } catch (err:any) { setError(err?.response?.data?.detail || 'Could not delete this scan.') } }
  return <>
    <div className="page-header"><div><p className="eyebrow">Audit trail</p><h1>Scan History</h1><p>Every review, score and risk finding in one searchable engineering trail.</p></div><div className="header-status"><Clock3 size={16}/>{scans.length} saved scans</div></div>
    <section className="panel history-panel">{error&&<div className="error-box">{error}</div>}{loading?<div className="loading">Loading scan history...</div>:<div className="table-wrap"><table><thead><tr><th>Scan</th><th>Language</th><th>Health</th><th>Issues</th><th>Critical</th><th>High</th><th>Created</th><th></th></tr></thead><tbody>{scans.map(s=><tr key={s.id}><td><Link className="scan-link" to={`/scans/${s.id}`}><b>{s.title}</b><small>Scan #{s.id}</small></Link></td><td><span className="language-chip">{s.language}</span></td><td><span className={`score score-${s.score>=80?'good':s.score>=50?'warn':'bad'}`}>{s.score}/100</span></td><td>{s.issue_count}</td><td><span className="count-critical">{s.critical_count}</span></td><td><span className="count-high">{s.high_count}</span></td><td>{new Date(s.created_at).toLocaleString()}</td><td><button className="icon-btn" onClick={()=>void del(s.id)} title="Delete scan"><Trash2 size={16}/></button></td></tr>)}{!scans.length&&<tr><td colSpan={8} className="empty">No scans yet.</td></tr>}</tbody></table></div>}</section>
  </>
}
