import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { History, LayoutDashboard, LogOut, ScanSearch, ShieldCheck, Sparkles } from 'lucide-react'

export default function Layout() {
  const nav = useNavigate()
  const user = JSON.parse(localStorage.getItem('devguard_user') || '{}')
  const logout = () => {
    localStorage.removeItem('devguard_token')
    localStorage.removeItem('devguard_user')
    nav('/login')
  }
  const initial = String(user.name || user.email || 'D').trim().charAt(0).toUpperCase()

  return (
    <div className="app-shell reference-shell">
      <aside className="sidebar reference-sidebar">
        <div className="brand reference-brand">
          <div className="brand-mark"><ShieldCheck size={24}/></div>
          <div>
            <strong>DevGuard <em>AI</em></strong>
            <span>Secure code intelligence</span>
          </div>
        </div>

        <nav className="reference-nav">
          <NavLink to="/" end><LayoutDashboard size={19}/><span>Dashboard</span></NavLink>
          <NavLink to="/scan"><ScanSearch size={19}/><span>New Scan</span></NavLink>
          <NavLink to="/history"><History size={19}/><span>Scan History</span></NavLink>
        </nav>

        <div className="sidebar-visual" aria-hidden="true">
          <div className="circuit c1"/><div className="circuit c2"/><div className="circuit c3"/>
          <div className="shield-orb"><ShieldCheck size={38}/></div>
        </div>

        <div className="sidebar-copy">
          <b>AI-Powered Code Security</b>
          <span>Automated scanning.<br/>Clear remediation.<br/>Stronger code.</span>
        </div>

        <div className="sidebar-spacer"/>

        <div className="engine-card">
          <div className="engine-card-head"><span className="status-dot"/><b>Analyzer online</b></div>
          <small>Security + quality engine ready</small>
        </div>

        <div className="sidebar-footer">
          <div className="user-chip refined">
            <div className="avatar">{initial}</div>
            <div><b>{user.name || 'Developer'}</b><span>{user.email || ''}</span></div>
          </div>
          <button className="ghost sidebar-signout" onClick={logout}><LogOut size={16}/> Sign out</button>
        </div>
      </aside>

      <div className="workspace reference-workspace">
        <main className="main reference-main"><Outlet/></main>
      </div>
    </div>
  )
}
