import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle, ArrowRight, Bell, Braces, Bug, CalendarDays, ChevronRight,
  FileJson, FileSpreadsheet, FileText, Gauge, History, ScanSearch, ShieldCheck
} from 'lucide-react'
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis
} from 'recharts'
import { api } from '../api/client'
import type { DashboardStats, Issue, Scan } from '../types'
import ExportModal from '../components/ExportModal'
import SeverityBadge from '../components/SeverityBadge'

const severityColors: Record<string,string> = {
  critical:'#ef5362', high:'#ff884d', medium:'#f2bb3b', low:'#41b9ba', info:'#5f8df2'
}

function Sparkline({color='#6279f4', reverse=false}:{color?:string,reverse?:boolean}) {
  const points = reverse
    ? '1,7 8,5 15,8 22,6 29,11 36,9 43,13 50,10 57,15 64,12'
    : '1,14 8,11 15,12 22,8 29,10 36,6 43,8 50,4 57,5 64,1'
  return <svg className="sparkline" viewBox="0 0 66 18" preserveAspectRatio="none">
    <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={points}/>
  </svg>
}

function Metric({
  icon,label,value,note,color='violet',reverse=false
}:{icon:ReactNode,label:string,value:string|number,note:string,color?:string,reverse?:boolean}) {
  return <article className="reference-metric">
    <div className={`reference-metric-icon ${color}`}>{icon}</div>
    <div className="reference-metric-copy">
      <span>{label}</span><strong>{value}</strong><small>{note}</small>
    </div>
    <Sparkline color={color==='danger'?'#ef5362':color==='cyan'?'#26aeca':color==='green'?'#25b88a':'#7866ef'} reverse={reverse}/>
  </article>
}

const fmtCards = [
  {label:'PDF',icon:FileText,tone:'pdf'},
  {label:'JSON',icon:FileJson,tone:'json'},
  {label:'CSV',icon:FileSpreadsheet,tone:'csv'},
  {label:'Markdown',icon:FileText,tone:'md'},
  {label:'HTML',icon:Braces,tone:'html'},
  {label:'TXT',icon:FileText,tone:'txt'},
]

export default function DashboardPage() {
  const [stats,setStats] = useState<DashboardStats|null>(null)
  const [latest,setLatest] = useState<Scan|null>(null)
  const [exportOpen,setExportOpen] = useState(false)
  const user = JSON.parse(localStorage.getItem('devguard_user') || '{}')

  useEffect(() => {
    let active = true
    api.get('/scans/dashboard').then(async r => {
      if (!active) return
      setStats(r.data)
      const id = r.data?.recent_scans?.[0]?.id
      if (id) {
        try {
          const detail = await api.get(`/scans/${id}`)
          if (active) setLatest(detail.data)
        } catch {}
      }
    }).catch(()=>{})
    return () => { active = false }
  }, [])

  const sev = Object.entries(stats?.severity_counts || {}).map(([name,value])=>({name,value:Number(value)}))
  const cats = Object.entries(stats?.category_counts || {})
    .map(([name,value])=>({name,value:Number(value)}))
    .sort((a,b)=>b.value-a.value).slice(0,5)

  const trend = useMemo(() => {
    const scans = [...(stats?.recent_scans || [])].reverse()
    return scans.map((s,i)=>({
      name: scans.length <= 5 ? `#${s.id}` : String(i+1),
      score: s.score
    }))
  },[stats])

  const highRisk=(stats?.severity_counts?.high||0)+(stats?.severity_counts?.critical||0)
  const avg=Math.round(stats?.average_score ?? 0)
  const topFindings: Issue[] = (latest?.issues || []).slice(0,5)

  return <>
    <header className="reference-dashboard-header">
      <div>
        <h1>Developer Security Dashboard</h1>
        <p>Review your code, prioritize risks, and track security quality over time.</p>
      </div>
      <div className="reference-header-actions">
        <div className="date-pill"><CalendarDays size={16}/> Latest activity</div>
        <Link to="/scan" className="primary reference-new-scan"><span>＋</span> New Code Scan</Link>
        <button className="round-action" aria-label="Notifications"><Bell size={18}/></button>
        <div className="header-user">
          <div className="header-avatar">{String(user.name||'M').charAt(0).toUpperCase()}</div>
          <div><b>{user.name||'Developer'}</b><small>Security workspace</small></div>
        </div>
      </div>
    </header>

    <section className="reference-metric-grid">
      <Metric icon={<ScanSearch/>} label="Total Scans" value={stats?.total_scans ?? 0} note="↑ saved reviews" color="violet"/>
      <Metric icon={<ShieldCheck/>} label="Average Score" value={`${avg}/100`} note="↑ code health baseline" color="green"/>
      <Metric icon={<Bug/>} label="Issues Found" value={stats?.total_issues ?? 0} note="all detected findings" color="cyan"/>
      <Metric icon={<AlertTriangle/>} label="High + Critical" value={highRisk} note="priority risks" color="danger" reverse/>
    </section>

    <section className="reference-analytics-grid">
      <article className="reference-card analytics-card">
        <div className="reference-card-title"><h2>Severity Distribution</h2><span>ⓘ</span></div>
        {sev.length ? <div className="reference-pie-wrap">
          <div className="reference-pie">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={sev} dataKey="value" nameKey="name" innerRadius={54} outerRadius={76} paddingAngle={1}>
                  {sev.map((x,i)=><Cell key={i} fill={severityColors[x.name] || '#5f8df2'}/>)}
                </Pie>
                <Tooltip contentStyle={{background:'#fff',border:'1px solid #d9e4f3',borderRadius:10,color:'#17233a'}}/>
              </PieChart>
            </ResponsiveContainer>
            <div className="pie-center"><strong>{stats?.total_issues||0}</strong><span>Total Issues</span></div>
          </div>
          <div className="severity-legend">
            {sev.map((x,i)=><div key={i}><span className="legend-dot" style={{background:severityColors[x.name]||'#5f8df2'}}/><b>{x.name}</b><span>{x.value}</span></div>)}
          </div>
        </div> : <Empty/>}
      </article>

      <article className="reference-card analytics-card">
        <div className="reference-card-title"><h2>Top Issue Categories</h2><span>ⓘ</span></div>
        {cats.length ? <div className="reference-bar-chart"><ResponsiveContainer>
          <BarChart data={cats} layout="vertical" margin={{left:6,right:22,top:5,bottom:5}}>
            <CartesianGrid stroke="#e9eff7" horizontal={false}/>
            <XAxis type="number" stroke="#8795aa" tickLine={false} axisLine={false}/>
            <YAxis type="category" dataKey="name" width={100} stroke="#6f7d91" tickLine={false} axisLine={false} tick={{fontSize:10}}/>
            <Tooltip contentStyle={{background:'#fff',border:'1px solid #d9e4f3',borderRadius:10,color:'#17233a'}}/>
            <Bar dataKey="value" fill="#7764ee" radius={[0,7,7,0]}/>
          </BarChart>
        </ResponsiveContainer></div> : <Empty/>}
      </article>

      <article className="reference-card analytics-card">
        <div className="reference-card-title"><h2>Code Quality Trend</h2><span>ⓘ</span></div>
        {trend.length ? <div className="reference-line-chart"><ResponsiveContainer>
          <LineChart data={trend} margin={{left:4,right:12,top:12,bottom:4}}>
            <CartesianGrid stroke="#e9eff7" vertical={false}/>
            <XAxis dataKey="name" stroke="#8795aa" tickLine={false} axisLine={false}/>
            <YAxis domain={[0,100]} stroke="#8795aa" tickLine={false} axisLine={false}/>
            <Tooltip contentStyle={{background:'#fff',border:'1px solid #d9e4f3',borderRadius:10,color:'#17233a'}}/>
            <Line type="monotone" dataKey="score" stroke="#7564ef" strokeWidth={3} dot={{r:4,fill:'#fff',stroke:'#7564ef',strokeWidth:2}}/>
          </LineChart>
        </ResponsiveContainer></div> : <Empty/>}
      </article>
    </section>

    <section className="reference-bottom-grid">
      <article className="reference-card recent-card">
        <div className="reference-card-title">
          <h2>Recent Scans</h2>
          <Link to="/history">View all scans <ArrowRight size={14}/></Link>
        </div>
        <div className="table-wrap">
          <table className="reference-table">
            <thead><tr><th>Project</th><th>Language</th><th>Score</th><th>Issues</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>
              {stats?.recent_scans?.slice(0,5).map(s=><tr key={s.id}>
                <td><Link to={`/scans/${s.id}`}><b>{s.title}</b></Link></td>
                <td><span className="language-chip">{s.language}</span></td>
                <td><span className={`score score-${s.score>=80?'good':s.score>=50?'warn':'bad'}`}>{s.score}</span></td>
                <td>{s.issue_count}</td>
                <td>{new Date(s.created_at).toLocaleDateString()}</td>
                <td><span className="completed-chip">Completed</span></td>
              </tr>)}
              {!stats?.recent_scans?.length && <tr><td colSpan={6}><Empty/></td></tr>}
            </tbody>
          </table>
        </div>
      </article>

      <article className="reference-card findings-summary-card">
        <div className="reference-card-title">
          <h2>Top Findings</h2>
          {latest && <Link to={`/scans/${latest.id}`}>View all <ArrowRight size={14}/></Link>}
        </div>
        <div className="dashboard-findings">
          {topFindings.map(i=><Link to={`/scans/${latest?.id}`} className="dashboard-finding" key={i.id}>
            <span className={`finding-dot sev-bg-${i.severity}`}>!</span>
            <div><b>{i.title}</b><small>{i.rule_id} • {i.category}</small></div>
            <SeverityBadge severity={i.severity}/>
            <ChevronRight size={15}/>
          </Link>)}
          {!topFindings.length && <Empty/>}
        </div>
      </article>

      <article className="reference-card export-summary-card">
        <div className="reference-card-title"><div><h2>Export Report</h2><p>Download scan results in your preferred format.</p></div></div>
        <div className="dashboard-format-grid">
          {fmtCards.map(({label,icon:Icon,tone})=><button key={label} className={`dashboard-format ${tone}`} onClick={()=>latest&&setExportOpen(true)} disabled={!latest}>
            <Icon size={19}/><span>{label}</span>
          </button>)}
        </div>
        <button className="export-all-button" onClick={()=>latest&&setExportOpen(true)} disabled={!latest}>Choose report options <ArrowRight size={15}/></button>
      </article>
    </section>

    <Link to="/history" className="history-banner">
      <div className="history-banner-icon"><History size={25}/></div>
      <div><b>Scan History</b><span>View and manage past scans, compare results, and track security improvements over time.</span></div>
      <span className="history-open">Open Scan History <ArrowRight size={18}/></span>
    </Link>

    {exportOpen && latest && <ExportModal scanId={latest.id} title={latest.title} onClose={()=>setExportOpen(false)}/>}
  </>
}

function Empty(){return <div className="empty">No scan data yet. Run your first code review.</div>}
