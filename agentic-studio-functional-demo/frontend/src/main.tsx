import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  BrainCircuit, CheckCircle2, CloudRain, Gauge,
  LockKeyhole, Play, RefreshCcw, ShieldCheck, Sparkles, UserCheck,
  Wind, XCircle, ArrowRight, Activity, Database, Clock3
} from 'lucide-react';
import './styles.css';

type Dashboard = any;
const API = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

const money = (v:number) => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', maximumFractionDigits:0}).format(v);

function App(){
  const [screen, setScreen] = useState<'landing'|'auth'|'dashboard'>('landing');
  const [data, setData] = useState<Dashboard|null>(null);
  const [analysis, setAnalysis] = useState<any|null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Connecting to Digital Twin API...');

  const load = async () => {
    try {
      const r = await fetch(`${API}/api/dashboard`);
      if (!r.ok) throw new Error('Dashboard unavailable');
      const dashboard = await r.json();
      setData(dashboard);
      setAnalysis((previous:any) =>
        previous?.approval?.id === dashboard.approval.id &&
        ['PENDING', 'APPROVE', 'REJECT'].includes(dashboard.approval.status)
          ? previous : null
      );
      return true;
    } catch {
      setAnalysis(null);
      setData((previous:Dashboard|null) => previous
        ? {...previous, approval: {...previous.approval, status: 'UNKNOWN'}} : previous);
      setMessage('Unable to refresh the dashboard. Check the backend connection.');
      return false;
    }
  };
  useEffect(()=>{ load(); },[]);

  const analyze = async () => {
    setBusy(true);
    setAnalysis(null);
    setMessage('Agents are analyzing Scene 42...');
    try {
      const res = await fetch(`${API}/api/scenes/42/analyze`, { method: 'POST' });
      if (!res.ok) {
        await load();
        setMessage(res.status === 409
          ? 'Analysis was reset or replaced. Review the current dashboard.'
          : 'Analysis failed. No new recommendation is available for approval.');
        return;
      }
      const analysisData = await res.json();
      setAnalysis(analysisData);
      await new Promise(r => setTimeout(r, 700));
      if (await load()) setMessage('Analysis complete. Review the current recommendation before deciding.');
    } catch {
      // The server may still be running; require a fresh dashboard before a decision.
      setData((previous:Dashboard|null) => previous
        ? {...previous, approval: {...previous.approval, status: 'UNKNOWN'}} : previous);
      setMessage('Analysis connection lost. Refresh the page before making a decision.');
    } finally {
      setBusy(false);
    }
  };
  const decide = async (decision:'approve'|'reject') => {
    const approvalId = data?.approval?.id;
    if (busy || !approvalId || data?.approval?.status !== 'PENDING') {
      setMessage('Run analysis and review a pending recommendation first.');
      return;
    }
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/approvals/${encodeURIComponent(approvalId)}`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({decision, actor:'Executive Producer'})
      });
      if (!r.ok) {
        setData((previous:Dashboard|null) => previous
          ? {...previous, approval: {...previous.approval, status: 'UNKNOWN'}} : previous);
        await load();
        setMessage(r.status === 409
          ? 'Recommendation changed or was already decided. Review the refreshed state.'
          : 'Decision was not accepted. Review the current state before trying again.');
        return;
      }
      const result = await r.json();
      setData((previous:Dashboard|null) => previous ? {
        ...previous, approval: result.approval, digital_twin: result.digital_twin
      } : previous);
      if (await load()) {
        setMessage(decision === 'approve'
          ? 'Approval recorded. Review the Digital Twin state for pending arrangements.'
          : 'Rejected. Existing production plan retained.');
      } else {
        setMessage('Decision recorded, but dashboard refresh failed. Refresh the page.');
      }
    } catch {
      setData((previous:Dashboard|null) => previous
        ? {...previous, approval: {...previous.approval, status: 'UNKNOWN'}} : previous);
      setMessage('Decision status could not be confirmed. Refresh before trying again.');
    } finally {
      setBusy(false);
    }
  };
  const reset = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/demo/reset`, {method:'POST'});
      if (!r.ok) throw new Error('Reset failed');
      setAnalysis(null);
      setData((previous:Dashboard|null) => previous
        ? {...previous, approval: {...previous.approval, status: 'AWAITING_ANALYSIS'}} : previous);
      if (await load()) setMessage('Demo reset. Run analysis before requesting approval.');
    } catch {
      setData((previous:Dashboard|null) => previous
        ? {...previous, approval: {...previous.approval, status: 'UNKNOWN'}} : previous);
      setMessage('Reset status could not be confirmed. Refresh the page.');
    } finally {
      setBusy(false);
    }
  };

  if(screen==='landing') return <Landing onLaunch={()=>setScreen('auth')} />;
  if(screen==='auth') return <Auth onSignIn={()=>setScreen('dashboard')} onBack={()=>setScreen('landing')} />;
  return <DashboardView data={data} analysis={analysis} busy={busy} message={message} analyze={analyze} decide={decide} reset={reset} />;
}

function Landing({onLaunch}:{onLaunch:()=>void}){
  return <main className="page landing">
    <nav className="topbar"><Brand/><div className="navlinks"><span>Product</span><span>Solutions</span><span>Technology</span><span>Resources</span><button className="ghost" onClick={onLaunch}>Sign In</button></div></nav>
    <section className="hero panel">
      <div className="hero-copy">
        <div className="eyebrow">ENTERPRISE PRODUCTION INTELLIGENCE</div>
        <h1>AGENTIC STUDIO<br/><em>DIGITAL TWIN</em></h1>
        <h2>AI-POWERED. HUMAN-LED. PRODUCTION READY.</h2>
        <p>A living digital twin of your film production. AI agents monitor changes, analyze impact, explain recommendations, and wait for human approval before changing the production state.</p>
        <div className="actions"><button className="primary" onClick={onLaunch}>Launch Platform <ArrowRight size={17}/></button><button className="ghost"><Play size={16}/> Watch Demo</button></div>
      </div>
      <div className="hero-visual">
        <div className="storm-orb"><CloudRain size={72}/><div className="grid-glow"></div></div>
        <div className="signal"><span>SCENE 42</span><strong>Weather risk detected</strong><small>Digital Twin event created</small></div>
      </div>
    </section>
    <section className="feature-grid">
      <Feature icon={<BrainCircuit/>} title="AI Agents" text="Monitor production in real time"/>
      <Feature icon={<Database/>} title="Digital Twin" text="One source of truth for every scene"/>
      <Feature icon={<UserCheck/>} title="Human in the Loop" text="You approve high-impact decisions"/>
      <Feature icon={<ShieldCheck/>} title="Physics & Safety" text="Model real-world production risk"/>
      <Feature icon={<Gauge/>} title="Business Impact" text="See cost and schedule consequences"/>
    </section>
    <footer>Built for Google Cloud • Gemini • Agentic workflows • FastAPI • React • PostgreSQL</footer>
  </main>
}

function Auth({onSignIn,onBack}:{onSignIn:()=>void,onBack:()=>void}){
  return <main className="page auth-page">
    <button className="back" onClick={onBack}>← Landing</button>
    <section className="auth-shell panel">
      <div className="auth-art"><CloudRain size={80}/><div><strong>Scene 42</strong><span>Secure production access</span></div></div>
      <form className="login" onSubmit={e=>{e.preventDefault();onSignIn();}}>
        <LockKeyhole size={38}/><h1>Welcome Back</h1><p>Sign in to Agentic Studio</p>
        <label>Email Address<input defaultValue="producer@studio.com" type="email"/></label>
        <label>Password<input defaultValue="agentic-demo" type="password"/></label>
        <label className="remember"><input type="checkbox" defaultChecked/> Remember me</label>
        <button className="primary wide" type="submit">Sign In</button>
        <small>Demo authentication only — no credentials are sent anywhere.</small>
      </form>
    </section>
  </main>
}

function DashboardView({data,analysis,busy,message,analyze,decide,reset}:{data:Dashboard|null,analysis:any|null,busy:boolean,message:string,analyze:()=>void,decide:(d:'approve'|'reject')=>void,reset:()=>void}){
  if(!data) return <main className="page centered"><div className="spinner"></div><p>Connecting to Digital Twin API...</p></main>;
  const pending = data.approval.status==='PENDING' && Boolean(data.approval.id);
  const approvalLabels:Record<string,string> = {
    PENDING: 'Producer Decision Required',
    APPROVE: 'Approved',
    REJECT: 'Rejected',
    AWAITING_ANALYSIS: 'Run Analysis First',
    ANALYZING: 'Analysis in Progress',
    ERROR: 'Analysis Failed — Retry Required',
    UNKNOWN: 'Refresh to Confirm Status',
  };
  const approvalLabel = approvalLabels[data.approval.status] || 'Refresh to Confirm Status';
  return <main className="page dashboard-page">
    <header className="dashboard-header"><Brand/><div><span className="live-dot"></span> Live &nbsp; <Clock3 size={15}/> 2:34 PM</div></header>
    <div className="dashboard-layout">
      <aside className="sidebar">
        {['Executive Overview','Scenes','Schedule','Weather Monitor','AI Agents','Physics & Safety','Business Impact','Approvals','Digital Twin','Reports','Audit Log','Settings'].map((x,i)=><div className={i===0?'active menu':'menu'} key={x}>{x}{x==='Approvals'&&pending?<b>1</b>:null}</div>)}
      </aside>
      <section className="content">
        <div className="title-row"><div><h1>Executive Overview</h1><p>Live Production Intelligence</p></div><div className="status-pill">{message}</div></div>
        <div className="kpis">
          <Kpi label="ACTIVE SCENES" value={data.kpis.active_scenes}/>
          <Kpi label="WEATHER ALERTS" value={data.kpis.weather_alerts} warn/>
          <Kpi label="PENDING APPROVALS" value={data.kpis.pending_approvals} warn/>
          <Kpi label="EST. IMPACT TODAY" value={money(data.kpis.estimated_impact_today)}/>
          <Kpi label="SCHEDULE IMPACT" value={`+${data.kpis.schedule_impact_hours} hrs`}/>
        </div>
        <div className="overview-grid">
          <section className="panel weather-card"><div className="card-head"><span>WEATHER EVENT IMPACTING PRODUCTION</span><b>HIGH IMPACT</b></div><h3>{data.scene.name}</h3><p>{data.scene.location}</p><div className="weather-stats"><CloudRain/><div><strong>Heavy Rain</strong><span>Wind {data.weather.wind_mph} mph • Lightning {data.weather.lightning_risk}</span></div></div><div className="timeline"><i></i><i></i><i className="hot"></i><i className="hot"></i><i></i><i></i></div></section>
          <section className="panel recommendation"><span>AI RECOMMENDATION</span><h3>{data.recommendation.action}</h3><ul>{data.recommendation.reasons.slice(0,3).map((r:string)=><li key={r}><CheckCircle2 size={14}/>{r}</li>)}</ul><button className="primary wide" onClick={analyze} disabled={busy}>{busy?'Analyzing...':'Run / Refresh Analysis'}</button></section>
          <section className="panel health"><span>PRODUCTION HEALTH</span><div className="health-ring">{data.kpis.production_health}%</div><small>Schedule 91% • Budget 92% • Resources 94%</small></section>
          <section className="panel activity"><span>AI AGENT ACTIVITY</span><p>Research Agent — retrieved weather data</p><p>Scheduling Agent — impact analysis complete</p><p>Budget Agent — cost impact analysis complete</p><p>Producer Agent — recommendation ready</p></section>
        </div>

        <div className="flow-title"><h2>HUMAN IN THE LOOP DECISION FLOW — SCENE 42 WEATHER EVENT</h2><button className="ghost" onClick={reset} disabled={busy}><RefreshCcw size={15}/> Reset Demo</button></div>
        <section className="flow">
          <Step n="1" title="DETECT & INGEST" icon={<CloudRain/>}><Agent name="Research Agent" sub="Parallel Search API"/><div className="mini-weather"><strong>Weather Data Retrieved</strong><span>Heavy rain</span><span>Wind: 32 mph</span><span>Lightning: High</span><span>Visibility: 2 mi</span></div><Metric label="Confidence" value="92%"/></Step>
          <Connector/>
          <Step n="2" title="SCHEDULING ASSESSMENT" icon={<Wind/>}><Agent name="Scheduling Agent" sub="Schedule Impact"/>{analysis ? (<div className="mini-weather"><strong>{analysis.evidence?.scheduling?.action || "Awaiting analysis"}</strong><span>{analysis.evidence?.scheduling?.reasoning || "Schedule impact has been reviewed."}</span></div>) : (<div className="mini-weather"><strong>Schedule Impact</strong><span>{data.recommendation?.reasons?.[1] || "Schedule impact reviewed."}</span></div>)}<Done/></Step>
          <Connector/>
          <Step n="3" title="BUDGET ASSESSMENT" icon={<ShieldCheck/>}><Agent name="Budget Agent" sub="Cost Impact"/>{analysis ? (<div className="mini-weather"><strong>{analysis.evidence?.budget?.estimated_cost || "Awaiting analysis"} — {analysis.evidence?.budget?.action || "Awaiting analysis"}</strong><span>{analysis.evidence?.budget?.reasoning || "Cost impact has been reviewed."}</span></div>) : (<div className="mini-weather"><strong>Cost Impact</strong><span>{data.recommendation?.reasons?.[2] || "Cost impact reviewed."}</span></div>)}</Step>
          <Connector/>
          <Step n="4" title="PRODUCER RECOMMENDATION" icon={<BrainCircuit/>}><Agent name="Producer Agent" sub="Synthesis & Recommendation"/><div className="recommended">{data.recommendation.action}</div><ul className="compact">{data.recommendation.reasons.map((r:string)=><li key={r}>✓ {r}</li>)}</ul><div className="impact"><span>Schedule <b>{analysis?.evidence?.scheduling?.action || "Awaiting analysis"}</b></span><span>Budget <b>{analysis?.evidence?.budget?.estimated_cost || "Awaiting analysis"}</b></span><span>Safety <b>Human review</b></span></div></Step>
          <Connector/>
          <Step n="5" title="HUMAN APPROVAL" icon={<UserCheck/>} hot={pending}><div className="human"><UserCheck size={42}/><strong>{approvalLabel}</strong></div><div className="decision-summary"><span>Decision</span><b>{data.recommendation.action}</b><div className="impact"><span>Schedule <b>{analysis?.evidence?.scheduling?.action || "Awaiting analysis"}</b></span><span>Budget <b>{analysis?.evidence?.budget?.estimated_cost || "Awaiting analysis"}</b></span><span>Safety <b>Human review</b></span></div></div><div className="decision-actions"><button className="reject" onClick={()=>decide('reject')} disabled={!pending||busy}><XCircle size={17}/> Reject</button><button className="approve" onClick={()=>decide('approve')} disabled={!pending||busy}><CheckCircle2 size={17}/> Approve</button></div></Step>
          <Connector/>
          <Step n="6" title="DIGITAL TWIN STATE" icon={<Database/>}><div className="twin-update"><strong>{data.digital_twin.decision_status || "Awaiting human decision"}</strong><p>Location <b>{data.digital_twin.location}</b></p><p>Schedule <b>{data.digital_twin.schedule}</b></p><p>Budget <b>{data.digital_twin.budget}</b></p><p>Crew <b>{data.digital_twin.crew}</b></p><p>Equipment <b>{data.digital_twin.equipment}</b></p><p>Safety <b>{data.digital_twin.safety}</b></p></div><small>Event history contains {data.events.length} recent events.</small></Step>
        </section>
      </section>
    </div>
  </main>
}

function Brand(){return <div className="brand"><div className="brand-icon">🎬</div><div><strong>AGENTIC STUDIO</strong><span>DIGITAL TWIN</span></div></div>}
function Feature({icon,title,text}:{icon:any,title:string,text:string}){return <div className="feature panel">{icon}<div><b>{title}</b><span>{text}</span></div></div>}
function Kpi({label,value,warn}:{label:string,value:any,warn?:boolean}){return <div className="kpi panel"><span>{label}</span><b className={warn?'warn':''}>{value}</b></div>}
function Step({n,title,icon,children,hot}:{n:string,title:string,icon:any,children:any,hot?:boolean}){return <article className={`step panel ${hot?'hot-step':''}`}><header><span className="num">{n}</span>{icon}<b>{title}</b></header>{children}</article>}
function Connector(){return <div className="connector"><ArrowRight size={18}/></div>}
function Agent({name,sub}:{name:string,sub:string}){return <div className="agent"><Sparkles size={19}/><div><b>{name}</b><span>{sub}</span></div></div>}
function Metric({label,value}:{label:string,value:string}){return <div className="metric"><span>{label}</span><b>{value}</b></div>}
function Done(){return <div className="done"><CheckCircle2 size={16}/> Analysis Complete</div>}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
