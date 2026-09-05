import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowRight, BrainCircuit, Clock, CloudRain, Database, Gauge, Home, RefreshCcw, Search, ShieldCheck, UserCheck, Wind } from 'lucide-react';
import './styles.css';

type Dashboard = any;
type Operation = 'analysis' | 'approve' | 'reject' | 'reset' | 'check' | null;
type DashboardTab = 'overview' | 'agents' | 'decision' | 'twin' | 'events';
const API = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';
const timestamp = (value?:string) => value
  ? new Date(value).toLocaleString(undefined, { timeZoneName: 'short' }) : 'Not recorded';
const safeSource = (value?:string) => {
  try { const url = new URL(value || ''); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; }
  catch { return null; }
};

function App() {
  const [screen, setScreen] = useState<'landing' | 'auth' | 'dashboard'>('landing');
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [data, setData] = useState<Dashboard | null>(null);
  const [operation, setOperation] = useState<Operation>(null);
  const [uncertain, setUncertain] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [message, setMessage] = useState('Connecting to the production dashboard...');
  const [tick, setTick] = useState(Date.now());
  const [localStart, setLocalStart] = useState<number | null>(null);
  const inFlight = useRef(false);
  const loadSequence = useRef(0);
  const mounted = useRef(true);

  const load = async () => {
    const sequence = ++loadSequence.current;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(`${API}/api/dashboard`, { signal: controller.signal, cache: 'no-store' });
      if (!response.ok) throw new Error('Dashboard unavailable');
      const dashboard = await response.json();
      if (!dashboard.approval || !dashboard.digital_twin) throw new Error('Invalid dashboard');
      if (mounted.current && sequence === loadSequence.current) {
        setData(dashboard); setUncertain(false); setLoaded(true);
      }
      return dashboard as Dashboard;
    } catch {
      if (mounted.current && sequence === loadSequence.current) {
        setUncertain(true); setLoaded(true);
        setMessage('Connection interrupted — outcome not confirmed. Check status before retrying.');
      }
      return null;
    } finally { window.clearTimeout(timer); }
  };

  useEffect(() => {
    mounted.current = true;
    void load().then(value => { if (value && mounted.current) setMessage('Dashboard connected.'); });
    return () => { mounted.current = false; ++loadSequence.current; };
  }, []);

  const serverRunning = data?.approval?.status === 'ANALYZING';
  useEffect(() => {
    if (operation !== 'analysis' && !serverRunning) return;
    const timer = window.setInterval(() => setTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [operation, serverRunning]);
  // Recover a running request discovered after reload without resubmitting it.
  useEffect(() => {
    if (!serverRunning || operation || uncertain) return;
    let stopped = false;
    let timer:number;
    const poll = async () => {
      const dashboard = await load();
      if (!stopped && dashboard?.approval?.status === 'ANALYZING') timer = window.setTimeout(poll, 3000);
    };
    timer = window.setTimeout(poll, 3000);
    return () => { stopped = true; window.clearTimeout(timer); };
  }, [serverRunning, operation, uncertain]);

  const checkStatus = async () => {
    if (inFlight.current) return;
    inFlight.current = true; setOperation('check');
    setMessage('Checking the latest workflow status...');
    try { if (await load()) setMessage('Latest workflow state restored. Review it before deciding.'); }
    finally { inFlight.current = false; setOperation(null); }
  };

  const mutate = async (kind:Exclude<Operation, 'check' | null>) => {
    if (inFlight.current || uncertain || !data || serverRunning) return;
    const status = data.approval.status;
    const reviewed = data.analysis;
    if (kind === 'approve' || kind === 'reject') {
      if (status !== 'PENDING' || reviewed?.approval?.id !== data.approval.id ||
          reviewed?.steps?.[3]?.requires_human !== true ||
          !['proceed', 'relocate', 'reschedule'].includes(data.recommendation.schedule_action)) return;
    }
    if (kind === 'analysis' && status === 'PENDING' && !window.confirm(
      'Replace this pending recommendation? Its approval request will be invalidated. The Digital Twin will remain unchanged.',
    )) return;
    if (kind === 'reset' && ['PENDING', 'APPROVE', 'REJECT'].includes(status) && !window.confirm(
      'Reset this replay? The recommendation will be cleared and simulated production restored. Previous decisions remain in recent event history.',
    )) return;
    inFlight.current = true;
    ++loadSequence.current;
    setOperation(kind);
    if (kind === 'analysis') { setLocalStart(Date.now()); setTick(Date.now()); }
    const labels = { analysis: 'Historical replay analysis running...', approve: 'Recording your approval...',
      reject: 'Recording your rejection...', reset: 'Resetting the production simulation...' };
    setMessage(labels[kind]);
    const path = kind === 'analysis' ? '/api/scenes/42/analyze' : kind === 'reset'
      ? '/api/demo/reset' : `/api/approvals/${encodeURIComponent(data.approval.id)}`;
    const controller = new AbortController();
    // A browser timeout cancels waiting, not necessarily server execution.
    const timer = window.setTimeout(() => controller.abort(), kind === 'analysis' ? 120000 : 20000);
    try {
      const response = await fetch(`${API}${path}`, { method: 'POST', signal: controller.signal,
        ...(kind === 'approve' || kind === 'reject' ? {
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision: kind, actor: 'Executive Producer' }),
        } : {}),
      });
      // Always recover the current server snapshot; never display a stale POST body.
      const dashboard = await load();
      if (!dashboard) return;
      if (!response.ok) setMessage(response.status === 409
        ? 'Request not accepted because workflow state changed. Review the current status.'
        : 'Request did not complete successfully. Review the current status below.');
      else setMessage(kind === 'analysis' ? 'Analysis request finished. Review the current evidence and recommendation.'
        : kind === 'approve' ? 'Approval recorded. Review pending arrangements in the Digital Twin.'
        : kind === 'reject' ? 'Recommendation rejected — production state unchanged.'
        : 'Replay reset — run a new analysis before requesting approval.');
    } catch {
      setUncertain(true);
      setMessage('Connection interrupted — outcome not confirmed. The server may still be processing. Check status before retrying.');
    } finally { window.clearTimeout(timer); inFlight.current = false; setOperation(null); setLocalStart(null); }
  };

  if (screen === 'landing') return <main className="page landing">
    <header className="topbar"><Brand/><nav className="navlinks preserved-links" aria-label="Product navigation">
      <a href="#product">Product</a><a href="#solutions">Solutions</a><a href="#technology">Technology</a><a href="#resources">Resources</a>
      <button className="ghost" onClick={() => setScreen('auth')}>Demo Access</button>
    </nav></header>
    <section className="hero panel" id="product"><div className="hero-copy">
      <p className="eyebrow">PRODUCTION INTELLIGENCE · COMPETITION PROTOTYPE</p>
      <h1>AGENTIC STUDIO<br/><em>DIGITAL TWIN</em></h1>
      <h2>AI-POWERED. HUMAN-LED. PRODUCTION SIMULATION.</h2>
      <p>A digital twin prototype for fictional film production. Research, Scheduling, Budget, and Producer agents analyze impact, explain recommendations, and wait for human approval before changing the simulated production state.</p>
      <div className="replay-actions"><button className="primary" onClick={() => setScreen('auth')}>Launch Platform <ArrowRight size={17} aria-hidden="true"/></button></div>
      <p>No sign-in protection is implemented in this local prototype. Do not enter credentials.</p>
    </div><div className="hero-visual">
      <div className="storm-orb"><CloudRain size={72} aria-hidden="true"/><div className="grid-glow" aria-hidden="true"/></div>
      <div className="signal"><span>SCENE 42</span><strong>Weather-risk simulation</strong><small>Run analysis to create a recommendation</small></div>
    </div></section>
    <section className="feature-grid" id="solutions" aria-label="Product capabilities">
      <Feature icon={<BrainCircuit/>} title="Four AI Agents" text="Research, Scheduling, Budget, and Producer analyze the scenario when requested; not continuous monitoring."/>
      <Feature icon={<Database/>} title="Digital Twin" text="Review the simulated Scene 42 production state before and after a human decision."/>
      <Feature icon={<UserCheck/>} title="Human in the Loop" text="Approve or reject the specific recommendation you reviewed."/>
      <Feature icon={<ShieldCheck/>} title="Weather Safety Guardrails" text="Implemented severe-weather rules constrain scheduling recommendations. They are not a separate agent or safety certification."/>
      <Feature icon={<Gauge/>} title="Business Impact" text="Review proposed scheduling actions and clearly labeled planning estimates, not committed costs."/>
    </section>
    <section className="panel landing-resources" id="resources"><h2>Resources</h2>
      <p>Open the production simulation to inspect returned source links, excerpts, and recent event history. The demo video is not available yet.</p>
      <FutureCapabilities/>
    </section>
    <footer id="technology">Google Cloud · Gemini · Parallel Search · Agentic workflows · FastAPI · React
      <p>State and recent history are currently held in memory. PostgreSQL persistence is not implemented in this prototype.</p></footer>
  </main>;
  if (screen === 'auth') return <main className="page auth-page">
    <button className="back" onClick={() => setScreen('landing')}>Back to overview</button>
    <section className="auth-shell panel">
      <div className="auth-art"><CloudRain size={80} aria-hidden="true"/><div><strong>Scene 42</strong><span>Production simulation access</span></div></div>
      <div className="login"><UserCheck size={38} aria-hidden="true"/><h1>Welcome Back</h1><h2>Demo access</h2><p>This is not authentication. No account or password is required.</p>
      <p>Do not enter real credentials or confidential production information.</p>
      <button className="primary wide" onClick={() => setScreen('dashboard')}>Enter Production Simulation</button>
      <small>Account sign-in and Remember me are unavailable. No credentials are collected.</small></div></section>
  </main>;
  if (!data) return <main className="page centered"><h1>{loaded ? 'Dashboard unavailable' : 'Connecting to the production dashboard...'}</h1>
    <p role="status">{message}</p><button className="primary" disabled={Boolean(operation) || !loaded} onClick={checkStatus}>Check Connection</button></main>;

  const status = uncertain ? 'UNKNOWN' : operation === 'analysis' ? 'ANALYZING' : data.approval.status;
  const current = data.analysis?.approval?.id === data.approval.id ? data.analysis : null;
  const result = operation === 'analysis' ? null : current;
  const evidence = result?.evidence;
  const research = evidence?.research;
  const scenario = data.scenario;
  const historical = scenario?.evidence_mode === 'historical_replay';
  const meta = scenario?.historical_metadata;
  const ready = status === 'AWAITING_ANALYSIS';
  const running = status === 'ANALYZING';
  const failed = status === 'ERROR';
  const pending = status === 'PENDING';
  const canDecide = pending && Boolean(result) && result?.steps?.[3]?.requires_human === true &&
    ['proceed', 'relocate', 'reschedule'].includes(data.recommendation.schedule_action) && !operation;
  const busy = Boolean(operation);
  const start = serverRunning ? Date.parse(data.attempt?.started_at || '') : localStart;
  const seconds = start && Number.isFinite(start) ? Math.max(0, Math.floor((tick - start) / 1000)) : 0;
  const elapsed = `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
  const statusLabels:Record<string, string> = { AWAITING_ANALYSIS: 'Ready to analyze the scenario', ANALYZING: 'Workflow running',
    ERROR: 'Analysis could not complete', PENDING: 'Human decision required', APPROVE: 'Approved',
    REJECT: 'Rejected — production state unchanged', UNKNOWN: 'Outcome not confirmed' };
  const agentState = (index:number) => running ? 'Workflow running — individual progress unavailable'
    : uncertain ? 'Current status unconfirmed' : failed ? 'No completed result available for this attempt'
    : result?.steps?.[index]?.status === 'complete' ? result.mode === 'demo' ? 'Simulated result available' : 'Result available' : 'Not yet analyzed';
  const source = safeSource(research?.source_url);
  const analysisLabel = failed ? 'Retry Analysis' : ready ? historical ? 'Run Replay Analysis' : 'Run Demo Analysis' : 'Run New Analysis';
  const estimateStatus = uncertain ? 'Unconfirmed' : running ? 'Analysis in progress'
    : failed ? 'Unavailable for this attempt' : result?.recommendation?.estimated_cost
      || (result ? data.recommendation.estimated_cost : 'Not analyzed');
  const evidenceStatus = uncertain ? 'Unconfirmed' : running ? 'In progress'
    : failed ? 'No completed evidence available' : !result ? 'Not analyzed'
    : result.mode === 'demo' ? 'Simulated results'
    : source && research?.excerpt ? 'Candidate — human verification required' : 'Exact-event evidence not confirmed';
  const safetyStatus = `${data.digital_twin.safety}${uncertain ? ' — last retrieved; current state unconfirmed' : ''}`;
  const recommendationTitle = running ? 'Analysis in progress' : uncertain ? 'Check status before deciding'
    : failed ? 'Analysis failed — retry required' : data.recommendation.action;
  const showCheckStatus = uncertain || failed || (serverRunning && operation !== 'analysis');
  const tabs:{id:DashboardTab; label:string; mobileLabel:string; icon:React.ReactNode}[] = [
    { id: 'overview', label: 'Overview', mobileLabel: 'Overview', icon: <Home aria-hidden="true"/> },
    { id: 'agents', label: 'AI Agent Analysis', mobileLabel: 'Analysis', icon: <Search aria-hidden="true"/> },
    { id: 'decision', label: 'Human Decision', mobileLabel: 'Decision', icon: <UserCheck aria-hidden="true"/> },
    { id: 'twin', label: 'Digital Twin', mobileLabel: 'Twin', icon: <Database aria-hidden="true"/> },
    { id: 'events', label: 'Recent Events', mobileLabel: 'Events', icon: <Clock aria-hidden="true"/> },
  ];
  const positionTab = (tab:DashboardTab) => {
    setActiveTab(tab);
    window.requestAnimationFrame(() => {
      document.getElementById('executive-overview')?.scrollIntoView({ block: 'start', behavior: 'auto' });
    });
  };
  const backToTop = () => {
    document.getElementById('executive-overview')?.scrollIntoView({ block: 'start', behavior: 'auto' });
  };
  const selectAdjacentTab = (event:React.KeyboardEvent<HTMLButtonElement>, index:number) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1
      : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    positionTab(tabs[next].id);
    const buttons = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
    buttons?.[next]?.focus();
  };

  return <main className="page dashboard-page">
    <header className="dashboard-header"><Brand/><span>{data.execution_mode === 'live' ? 'Live execution configured' : 'Demo execution — simulated responses'}</span></header>
    <section className="content replay-content" id="executive-overview"><h1>Executive Overview</h1><p>Production decision review — Scene 42</p>
      <nav className="dashboard-navigation" aria-label="Dashboard views">
        <div className="dashboard-tabs" role="tablist" aria-label="Dashboard views">
          {tabs.map((tab, index) => <button key={tab.id} id={`tab-${tab.id}`} role="tab"
            aria-selected={activeTab === tab.id} aria-controls={`panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1} onKeyDown={event => selectAdjacentTab(event, index)}
            onClick={() => positionTab(tab.id)}>{tab.label}</button>)}
        </div>
      </nav>
      <section className="panel replay-banner" id="weather-context" aria-label="Scenario context">
        <span className="replay-banner-icon" aria-hidden="true">🎬</span>
        <div><strong>{historical ? 'Fictional replay, not a live alert.' : 'Controlled fictional production demo.'}</strong>
          <p>{historical ? `This simulated production scenario is built on a historical weather event (${meta.area}, ${scenario.event_date}, ${meta.event_time_local} local time).` : 'This is a fictional weather disruption scenario.'}</p>
          <p>No real filming, budget, crew, or schedule is affected by this demonstration.</p>
        </div>
      </section>

      <section id="panel-overview" role="tabpanel" aria-labelledby="tab-overview" hidden={activeTab !== 'overview'}>
      <section className={`panel replay-controls ${failed || uncertain ? 'status-warning' : ''}`} aria-label="Workflow status and actions">
        <div role="status" aria-live="polite" aria-atomic="true"><h2>{statusLabels[status] || 'Check workflow status'}</h2><p>{message}</p></div>
        {running && <><p>Elapsed: <time>{elapsed}</time></p><p>No production changes have been applied by this analysis.</p>
          {seconds >= 60 && <p>This is taking longer. You do not need to submit again.</p>}</>}
        {failed && <p>No recommendation from this attempt is available for approval. Existing Digital Twin state is preserved.
          {' '}Support reference: <code>{data.attempt?.reference || 'Unavailable'}</code></p>}
        {uncertain && <p>The server may still be processing. Decisions and new analysis are disabled until status is confirmed.</p>}
        <div className="replay-actions">
          <button className="primary" disabled={busy || running || uncertain} onClick={() => mutate('analysis')}>{operation === 'analysis' ? 'Analyzing...' : analysisLabel}</button>
          {showCheckStatus && <button className="ghost" disabled={busy} onClick={checkStatus}>{operation === 'check' ? 'Checking...' : 'Check Status'}</button>}
          <button className="ghost" disabled={busy || running || uncertain || ready} onClick={() => mutate('reset')}><RefreshCcw size={16} aria-hidden="true"/>{operation === 'reset' ? 'Resetting...' : 'Reset Replay'}</button>
          {pending && <button className="ghost" onClick={() => positionTab('decision')}>Review decision</button>}
          {['APPROVE', 'REJECT'].includes(status) && <button className="ghost" onClick={() => positionTab('twin')}>View Digital Twin</button>}
        </div>
      </section>
      <section className={`panel decision-hero ${pending ? 'decision-required' : ''}`} aria-label="Current recommendation">
        <span className="state-badge">{pending ? 'Human decision required' : statusLabels[status] || 'Workflow status'}</span>
        <h2>{recommendationTitle}</h2>
        <p>{result ? 'Recommended by the Producer Agent after the four-agent analysis.' : 'Run the four-agent analysis to produce a reviewable recommendation.'}</p>
        <div className="fact-grid">
          <Fact label="Estimated planning impact" value={estimateStatus}/>
          <Fact label="Safety state" value={safetyStatus} risk/>
          <Fact label="Evidence status" value={evidenceStatus}/>
        </div>
        {pending && <div className="decision-actions overview-decision-actions">
          <button className="approve" disabled={!canDecide} onClick={() => positionTab('decision')}>Review approval</button>
          <button className="reject" disabled={!canDecide} onClick={() => positionTab('decision')}>Review rejection</button>
        </div>}
        <p className="fine-print">Approving records the selected response only. It does not book a date or location, commit the estimate, spend money, or certify that conditions are safe.</p>
      </section>
      <div className="replay-overview">
        <section className="panel" id="scenario"><h2>Scenario assumptions</h2><h3>Scene 42 — fictional exterior filming</h3>
          <p>{historical ? `${meta.area} ${meta.tornado_rating} tornado · ${scenario.event_date}` : 'Controlled demo inputs, not observed conditions'}</p>
          {historical && <p>Scenario wind input: {meta.estimated_max_wind_mph} mph — supplied event-maximum estimate, not a measurement at the fictional set. Verify it against a source before treating it as documented fact.</p>}
          <p>Severe-weather guardrails support human review; they are not a physics simulation or safety certification.</p>
        </section>
        <section className="panel"><h2>How the decision is produced</h2><p>Four automated agents propose a response in sequence: Research, Scheduling, Budget, and Producer.</p>
          <p>A person—not another agent—approves or rejects the reviewed recommendation.</p>
          <button className="ghost" onClick={() => positionTab('agents')}>Review the four agents</button></section>
      </div>
      </section>

      <section id="panel-agents" role="tabpanel" aria-labelledby="tab-agents" hidden={activeTab !== 'agents'}>
      <h2>Decision workflow — Scene 42</h2>
      <p>Four AI agents: Research, Scheduling, Budget, and Producer. Step 5 is a human decision; step 6 is the resulting Digital Twin state. Neither is an additional agent.</p>
      <section className="agent-grid" id="agent-results" aria-label="Four-agent results">
        <Step number={1} title="Historical Evidence" icon={<CloudRain/>}><h3>Research Agent</h3><p className="agent-status">{agentState(0)}</p>
          {research ? <><p>Provider: Parallel Search</p><p>Verification: {source && research.excerpt ? 'Candidate evidence — human source review required' : 'Exact-event evidence not confirmed'}</p>
            {source && <p><a href={source} target="_blank" rel="noopener noreferrer">Open retrieved source: {source}</a></p>}
            <p>Retrieved at: {timestamp(research.retrieved_at)}</p>
            <Details label="Read source excerpt"><pre className="source-excerpt">{research.excerpt || 'No matching excerpt returned.'}</pre></Details>
            <Details label="Read AI research summary"><p>{research.summary}</p></Details>
            <Details label="View research query"><p>{research.query}</p></Details></>
            : <p>{result?.mode === 'demo' ? 'Simulated research; no source was retrieved.' : 'Historical evidence is not available for this analysis.'}</p>}
        </Step>
        <Step number={2} title="Scheduling Assessment" icon={<Wind/>} id="scheduling-assessment"><h3>Scheduling Agent</h3><p className="agent-status">{agentState(1)}</p>
          {result && <><p>Proposed action: <strong>{data.recommendation.schedule_action}</strong></p>
            <Details label="View scheduling reasoning"><p>{evidence?.scheduling?.reasoning || 'Simulated scheduling assessment.'}</p><p>Scenario inputs are not independently verified measurements. This is not a current emergency alert.</p></Details></>}
        </Step>
        <Step number={3} title="Budget Assessment" icon={<ShieldCheck/>} id="budget-assessment"><h3>Budget Agent</h3><p className="agent-status">{agentState(2)}</p>
          {result && <><p>Estimated planning impact: <strong>{data.recommendation.estimated_cost}</strong></p><p>Advisory estimate only — not spending authorization.</p>
            <Details label="View budget reasoning"><p>{evidence?.budget?.reasoning || 'Simulated budget estimate.'}</p>
              {evidence?.budget?.action && <p>Agent advisory classification: {evidence.budget.action}. This is not a human approval.</p>}</Details></>}
        </Step>
        <Step number={4} title="Producer Recommendation" icon={<BrainCircuit/>}><h3>Producer Agent</h3><p className="agent-status">{agentState(3)}</p>
          <p><strong>{running ? 'Analysis in progress' : uncertain ? 'Status unconfirmed' : data.recommendation.action}</strong></p>
          {result && <Details label="View producer summary and rationale"><p>Original AI output — review against the source. Costs remain estimates regardless of generated wording.</p><p>{evidence?.producer?.summary}</p><p>{evidence?.producer?.rationale || data.recommendation.explanation}</p></Details>}
        </Step>
      </section>
      </section>

      <section id="panel-decision" role="tabpanel" aria-labelledby="tab-decision" hidden={activeTab !== 'decision'}>
        <p className="section-kicker">HUMAN DECISION</p><h2>Your call, not the agents’</h2>
        <p>The four agents propose. Nothing is booked, spent, or scheduled until you act here.</p>
        <Step number={5} title="Human Decision — not an agent" icon={<UserCheck/>} id="human-decision"><h3>{statusLabels[status] || 'Check status'}</h3>
          <p>{running ? 'Analysis in progress' : data.recommendation.action}</p>
          <div className="fact-grid compact-facts"><Fact label="Estimated planning impact" value={estimateStatus}/><Fact label="Safety state" value={safetyStatus} risk/><Fact label="Evidence status" value={evidenceStatus}/></div>
          <p>Approval records the selected production response. It does not book a date or location, commit the estimated cost, or establish that conditions are safe.</p>
          {pending && !result && <p>Reviewable evidence is unavailable. Check Status before deciding.</p>}
          {result && <p>Evidence status: {result.mode === 'demo' ? 'Simulated results' : source && research?.excerpt ? 'Candidate source — human verification required' : 'Not confirmed; do not treat scenario assumptions as verified facts'}</p>}
          {['APPROVE', 'REJECT'].includes(status) && <p>Recorded by {data.approval.actor} · {timestamp(data.approval.decided_at)}</p>}
          <div className="decision-actions"><button className="reject" disabled={!canDecide} onClick={() => mutate('reject')}>{operation === 'reject' ? 'Recording rejection...' : 'Reject'}</button>
            <button className="approve" disabled={!canDecide} onClick={() => mutate('approve')}>{operation === 'approve' ? 'Recording approval...' : 'Approve'}</button></div>
          {!pending && <p>Decision controls require a current pending recommendation.</p>}
        </Step>
      </section>

      <section id="panel-twin" role="tabpanel" aria-labelledby="tab-twin" hidden={activeTab !== 'twin'}>
        <p className="section-kicker">SYSTEM RECORD</p><h2>Digital Twin state</h2><p>What is recorded after a human decision. This is not an agent.</p>
        <Step number={6} title="Digital Twin State — not an agent" icon={<Database/>} id="twin-state"><h3>{data.digital_twin.decision_status}</h3>
          <p>Recorded production simulation state{uncertain ? ' — last retrieved; current state unconfirmed' : ''}.</p>
          <dl className="twin-fields">{['location', 'schedule', 'budget', 'crew', 'equipment', 'safety'].map(field =>
            <React.Fragment key={field}><dt>{field}</dt><dd className={field === 'safety' ? 'risk-high' : ''}>{data.digital_twin[field]}</dd></React.Fragment>)}</dl>
          <p>Last updated: {timestamp(data.digital_twin.last_updated)}</p>
        </Step>
      </section>

      <section id="panel-events" role="tabpanel" aria-labelledby="tab-events" hidden={activeTab !== 'events'}>
        <p className="section-kicker">RECENT EVENTS</p><h2>Workflow history</h2><p>Recent in-memory history only; not permanent audit storage.</p>
        <section className="panel event-history" id="recent-events">
          {data.events.length ? <ol>{data.events.map((event:any) => <li key={event.id}><time>{timestamp(event.time)}</time><span>{event.message}</span></li>)}</ol>
            : <p>No workflow events have been recorded yet.</p>}
        </section>
      </section>
      <button className="back-to-top" type="button" onClick={backToTop} aria-label="Back to top of dashboard">↑ Back to top</button>
    </section>
    <nav className="mobile-bottom-navigation" aria-label="Dashboard views">
      {tabs.map(tab => <button key={tab.id} type="button" aria-pressed={activeTab === tab.id}
        aria-label={tab.label} onClick={() => positionTab(tab.id)}>
        {tab.icon}<span>{tab.mobileLabel}</span>
      </button>)}
    </nav>
  </main>;
}

function Brand() { return <div className="brand"><span aria-hidden="true">🎬</span><div><strong>AGENTIC STUDIO</strong><span>DIGITAL TWIN</span></div></div>; }
function FutureCapabilities() {
  return <Details label="Future capabilities—not implemented">
    <p>These are broader product ideas, not working features or agents in this submission. The submitted workflow contains four agents: Research, Scheduling, Budget, and Producer.</p>
    <ul>
      <li>Multi-scene management, schedule editing, and continuous weather monitoring. This demo evaluates one fixed Scene 42 scenario on request.</li>
      <li>Physics simulation and additional specialist agents. The current safety protection is a deterministic scheduling guardrail, not a separate Physics or Safety Agent.</li>
      <li>Reports, configurable settings, account authentication, and persistent audit storage. Current event history is recent and in memory.</li>
    </ul>
    <p>The demonstration video is pending. No controls here launch unfinished capabilities.</p>
  </Details>;
}
function Feature({ icon, title, text }: { icon:React.ReactNode; title:string; text:string }) {
  return <article className="feature panel"><span aria-hidden="true">{icon}</span><div><b>{title}</b><span>{text}</span></div></article>;
}
function Step({ number, title, icon, children, id }: { number:number; title:string; icon:React.ReactNode; children:React.ReactNode; id?:string }) {
  return <article className="step panel" id={id} tabIndex={id ? -1 : undefined}><header><span className="num">{number}</span><span aria-hidden="true">{icon}</span><h2>{title}</h2></header>{children}</article>;
}
function Details({ label, children }: { label:string; children:React.ReactNode }) { return <details className="replay-details"><summary>{label}</summary>{children}</details>; }
function Fact({ label, value, risk=false }: { label:string; value:React.ReactNode; risk?:boolean }) {
  return <div className="decision-fact"><strong className={risk ? 'risk-high' : ''}>{value}</strong><span>{label}</span></div>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
