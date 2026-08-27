import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertTriangle, BrainCircuit, CheckCircle2, CloudRain, Gauge,
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
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Demo mode: no API keys required.');

  const load = async () => {
    try {
      const r = await fetch(`${API}/api/dashboard`);
      setData(await r.json());
    } catch {
      setMessage('Backend is not running. Start FastAPI on port 8000.');
    }
  };
  useEffect(()=>{ load(); },[]);

  const analyze = async () => {
    setBusy(true); setMessage('Agents are analyzing Scene 42...');
    await fetch(`${API}/api/scenes/42/analyze`, {method:'POST'});
    await new Promise(r=>setTimeout(r,700));
    await load(); setBusy(false); setMessage('Analysis complete. Human decision required.');
  };
  const decide = async (decision:'approve'|'reject') => {
    setBusy(true);
    const r = await fetch(`${API}/api/approvals/approval-scene-42-weather`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({decision, actor:'Executive Producer'})
    });
    if(!r.ok) setMessage('Decision failed. Check backend console.');
    else setMessage(decision==='approve' ? 'Approved. Digital Twin state propagated.' : 'Rejected. Existing plan retained.');
    await load(); setBusy(false);
  };
  const reset = async () => {
    await fetch(`${API}/api/demo/reset`, {method:'POST'}); await load();
    setMessage('Demo reset. Scene 42 is awaiting approval again.');
  };

  if(screen==='landing') return <Landing onLaunch={()=>setScreen('auth')} />;
  if(screen==='auth') return <Auth onSignIn={()=>setScreen('dashboard')} onBack={()=>setScreen('landing')} />;
  return <DashboardView data={data} busy={busy} message={message} analyze={analyze} decide={decide} reset={reset} />;
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

function DashboardView({data,busy,message,analyze,decide,reset}:{data:Dashboard|null,busy:boolean,message:string,analyze:()=>void,decide:(d:'approve'|'reject')=>void,reset:()=>void}){
  if(!data) return <main className="page centered"><div className="spinner"></div><p>Connecting to Digital Twin API...</p></main>;
  const pending = data.approval.status==='PENDING';
  const approved = data.approval.status==='APPROVE';
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
          <section className="panel recommendation"><span>AI RECOMMENDATION</span><h3>Move Scene 42 to Stage B</h3><ul>{data.recommendation.reasons.slice(0,3).map((r:string)=><li key={r}><CheckCircle2 size={14}/>{r}</li>)}</ul><button className="primary wide" onClick={analyze} disabled={busy}>{busy?'Analyzing...':'Run / Refresh Analysis'}</button></section>
          <section className="panel health"><span>PRODUCTION HEALTH</span><div className="health-ring">{data.kpis.production_health}%</div><small>Schedule 91% • Budget 92% • Resources 94%</small></section>
          <section className="panel activity"><span>AI AGENT ACTIVITY</span><p>Research Agent — retrieved weather data</p><p>Physics Agent — impact analysis complete</p><p>Safety Agent — risk evaluation complete</p><p>Producer Agent — recommendation ready</p></section>
        </div>

        <div className="flow-title"><h2>HUMAN IN THE LOOP DECISION FLOW — SCENE 42 WEATHER EVENT</h2><button className="ghost" onClick={reset}><RefreshCcw size={15}/> Reset Demo</button></div>
        <section className="flow">
          <Step n="1" title="DETECT & INGEST" icon={<CloudRain/>}><Agent name="Research Agent" sub="Parallel Search API"/><div className="mini-weather"><strong>Weather Data Retrieved</strong><span>Heavy rain</span><span>Wind: 32 mph</span><span>Lightning: High</span><span>Visibility: 2 mi</span></div><Metric label="Confidence" value="92%"/></Step>
          <Connector/>
          <Step n="2" title="PHYSICS ANALYSIS" icon={<Wind/>}><Agent name="Physics Agent" sub="Environmental Impact Model"/><div className="risk-list"><Risk label="Wind Load" value="HIGH"/><Risk label="Crane Stability" value="MEDIUM"/><Risk label="Surface Condition" value="WET"/><Risk label="Electrical Exposure" value="MEDIUM"/></div><Done/></Step>
          <Connector/>
          <Step n="3" title="SAFETY ASSESSMENT" icon={<ShieldCheck/>}><Agent name="Safety Agent" sub="Risk & Compliance"/><div className="hazard"><AlertTriangle size={44}/><strong>HIGH RISK</strong></div><div className="risk-list"><Risk label="Wind Exposure" value="HIGH"/><Risk label="Electrical Hazards" value="HIGH"/><Risk label="Slip Hazard" value="HIGH"/><Risk label="Equipment Risk" value="MEDIUM"/><Risk label="Crew Exposure" value="HIGH"/></div></Step>
          <Connector/>
          <Step n="4" title="PRODUCER RECOMMENDATION" icon={<BrainCircuit/>}><Agent name="Producer Agent" sub="Synthesis & Recommendation"/><div className="recommended">MOVE SCENE 42<br/>TO STAGE B</div><ul className="compact">{data.recommendation.reasons.map((r:string)=><li key={r}>✓ {r}</li>)}</ul><div className="impact"><span>Schedule <b>+2 hrs</b></span><span>Budget <b>+$11,700</b></span><span>Safety <b>LOW</b></span></div></Step>
          <Connector/>
          <Step n="5" title="HUMAN APPROVAL" icon={<UserCheck/>} hot={pending}><div className="human"><UserCheck size={42}/><strong>{pending?'Producer Decision Required':approved?'Approved':'Rejected'}</strong></div><div className="decision-summary"><span>Decision</span><b>Move Scene 42 to Stage B</b><div className="impact"><span>Schedule <b>+2 hrs</b></span><span>Budget <b>+$11,700</b></span><span>Safety <b>LOW</b></span></div></div><div className="decision-actions"><button className="reject" onClick={()=>decide('reject')} disabled={!pending||busy}><XCircle size={17}/> Reject</button><button className="approve" onClick={()=>decide('approve')} disabled={!pending||busy}><CheckCircle2 size={17}/> Approve</button></div></Step>
          <Connector/>
          <Step n="6" title="DIGITAL TWIN UPDATED" icon={<Database/>}><div className="twin-update"><strong>Scene 42 Update Propagated</strong><p>Location <b>{data.digital_twin.location}</b></p><p>Schedule <b>{data.digital_twin.schedule}</b></p><p>Budget <b>{data.digital_twin.budget}</b></p><p>Crew <b>{data.digital_twin.crew}</b></p><p>Equipment <b>{data.digital_twin.equipment}</b></p><p>Safety <b>{data.digital_twin.safety}</b></p></div><small>Event history contains {data.events.length} recent events.</small></Step>
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
function Risk({label,value}:{label:string,value:string}){return <p><span>{label}</span><b className={value==='HIGH'?'danger':value==='MEDIUM'?'medium':''}>{value}</b></p>}
function Metric({label,value}:{label:string,value:string}){return <div className="metric"><span>{label}</span><b>{value}</b></div>}
function Done(){return <div className="done"><CheckCircle2 size={16}/> Analysis Complete</div>}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
