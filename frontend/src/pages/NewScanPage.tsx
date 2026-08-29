import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Braces, CheckCircle2, Cpu, ScanSearch, ShieldCheck, Sparkles, WandSparkles } from 'lucide-react'
import { api } from '../api/client'

const samples: Record<string,string> = {
  python: `import subprocess\npassword = "supersecret123"\n\ndef run(cmd):\n    print("running", cmd)\n    subprocess.run(cmd, shell=True)\n    return eval(input("expression: "))\n`,
  javascript: `const apiKey = "secret-api-key-123";\nfunction render(input) {\n  document.getElementById('out').innerHTML = input;\n  console.log(apiKey);\n  return eval(input);\n}\n`,
}
export default function NewScanPage(){
  const [title,setTitle]=useState('Security review'); const [language,setLanguage]=useState('python'); const [code,setCode]=useState(samples.python); const [useLlm,setUseLlm]=useState(false); const [loading,setLoading]=useState(false); const [error,setError]=useState(''); const nav=useNavigate()
  const lines=useMemo(()=>code ? code.split('\n').length : 0,[code]); const chars=code.length
  const scan=async()=>{ if(!code.trim()) return; setLoading(true);setError(''); try{const r=await api.post('/scans',{title,language,code,use_llm:useLlm}); nav(`/scans/${r.data.id}`)}catch(e:any){setError(e.response?.data?.detail||'Scan failed')}finally{setLoading(false)}}
  const langChange=(v:string)=>{setLanguage(v);if(samples[v])setCode(samples[v])}
  return <>
    <div className="page-header"><div><p className="eyebrow">New analysis</p><h1>Review source code</h1><p>Run security and maintainability intelligence against code before it reaches production.</p></div><div className="header-status"><ShieldCheck size={16}/> Local analyzer ready</div></div>
    <div className="scan-layout">
      <section className="panel editor-panel">
        <div className="editor-toolbar"><div><Braces size={17}/><b>Source workspace</b></div><div className="editor-stats"><span>{language}</span><span>{lines} lines</span><span>{chars} chars</span></div></div>
        <div className="form-row"><label>Scan title<input value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Language<select value={language} onChange={e=>langChange(e.target.value)}><option value="python">Python</option><option value="javascript">JavaScript</option><option value="typescript">TypeScript</option><option value="java">Java</option><option value="generic">Generic</option></select></label></div>
        <label>Source code<textarea className="code-editor" value={code} onChange={e=>setCode(e.target.value)} spellCheck={false}/></label>
      </section>
      <aside className="panel scan-options"><div className="scan-orb"><ScanSearch size={30}/></div><p className="panel-kicker">Analysis stack</p><h2>Scan options</h2><p>The deterministic engine is always active and works without an API key.</p><div className="capability-list"><div><CheckCircle2/><span><b>Security rules</b><small>Credentials, injection, dangerous execution</small></span></div><div><CheckCircle2/><span><b>Quality rules</b><small>Debug code and maintainability risks</small></span></div><div><Cpu/><span><b>Local-first</b><small>Core analysis stays on your machine</small></span></div></div><label className="toggle premium-toggle"><input type="checkbox" checked={useLlm} onChange={e=>setUseLlm(e.target.checked)}/><span><b><WandSparkles size={15}/> AI deep review</b><small>Uses configured Ollama or OpenAI-compatible provider.</small></span></label>{error&&<div className="error-box">{error}</div>}<button className="primary full scan-button" onClick={scan} disabled={loading}><Sparkles size={18}/>{loading?'Analyzing code…':'Run DevGuard scan'}</button></aside>
    </div>
  </>
}
