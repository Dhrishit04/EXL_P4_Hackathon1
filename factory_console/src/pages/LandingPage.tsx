/* Public landing page that explains ModelPassport while banna's cursors build it on screen. */
import { useLayoutEffect, useState } from 'react'
import { Monitor, Moon, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiMode } from '../api/client'
import { useFactoryMetrics } from '../api/hooks'
import { startBuild, stopBuild } from '../components/useBuildIn'
import { formatCount } from '../formatting/formatNumbers'
import '../landing.css'

const stamps = [
  { name: 'Discover', output: 'Inventory record and risk tier for every model in the estate.', by: 'factory_core' },
  { name: 'Document', output: 'Current documentation where every claim cites code lines, plus the drift against the old document.', by: 'factory_core' },
  { name: 'Redevelop', output: 'Python rebuild of the SAS or R model, unit tests and a four level parity certificate.', by: 'redev_engine' },
  { name: 'Validate', output: 'Independent validation of discrimination, calibration, stability and fairness, with findings and a report.', by: 'validation_lab + factory_core' },
  { name: 'Monitor', output: 'Drift monitoring on production batches with an automatic revalidation trigger.', by: 'validation_lab + factory_core' },
]

const rules = [
  { title: 'Every claim is cited', text: 'Any sentence an agent writes about a model points to file and line evidence, and code checks that the evidence exists. Unverified claims are flagged, never hidden.' },
  { title: 'Every number is computed', text: 'No metric or coefficient comes from an LLM. Deterministic code computes the numbers; the words around them are checked against the results.' },
  { title: 'Every gate is signed', text: 'Agents never approve their own work. A human signs each gate in a tamper evident audit trail, and the validation approver cannot be the redevelopment approver.' },
  { title: 'Every failure is shown', text: 'A failed test or a parity mismatch is returned and shown in the console, never smoothed over.' },
]

const services = [
  { name: 'factory_console', role: 'This web console' },
  { name: 'factory_core', role: 'Agents, inventory, gates, audit' },
  { name: 'redev_engine', role: 'SAS and R to Python, parity proof' },
  { name: 'validation_lab', role: 'Metrics, fairness, monitoring' },
]

type Theme = 'light' | 'dark' | 'device'
const THEME_KEY = 'mp-landing-theme'
const themes = [
  { value: 'light', label: 'Light theme', Icon: Sun },
  { value: 'dark', label: 'Dark theme', Icon: Moon },
  { value: 'device', label: 'Device theme', Icon: Monitor },
] as const

/** Reads the saved landing theme; storage can be blocked, so it falls back to the device setting. */
function savedTheme(): Theme {
  try {
    const value = localStorage.getItem(THEME_KEY)
    if (value === 'light' || value === 'dark') return value
  } catch {
    // Storage unavailable: follow the device.
  }
  return 'device'
}

/** Renders the landing page and runs the full cursor build on it. */
export function LandingPage() {
  const [theme, setTheme] = useState<Theme>(savedTheme)
  const changeTheme = (value: Theme) => {
    setTheme(value)
    try {
      localStorage.setItem(THEME_KEY, value)
    } catch {
      // The choice still applies for this visit.
    }
  }

  useLayoutEffect(() => {
    startBuild()
    return stopBuild
  }, [])

  const rebuild = () => {
    window.scrollTo({ top: 0, behavior: 'instant' })
    startBuild()
  }

  return (
    <div className="landing" data-theme={theme}>
      <header className="top">
        <div className="wrap">
          <Link className="brand" to="/">
            <span className="brand-seal" aria-hidden="true">MP</span>ModelPassport
          </Link>
          <nav className="nav" aria-label="Landing">
            <a className="hide-phone" href="#problem">Why</a>
            <a className="hide-phone" href="#stamps">How it works</a>
            <a className="hide-phone" href="#rules">Rules</a>
            <Link to="/dashboard">Open console</Link>
            <div className="theme-pick" role="group" aria-label="Theme">
              {themes.map(({ value, label, Icon }) => (
                <button key={value} type="button" aria-label={label} title={label} aria-pressed={theme === value} onClick={() => changeTheme(value)}>
                  <Icon size={16} strokeWidth={2.2} aria-hidden="true" />
                </button>
              ))}
            </div>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="wrap">
            <div>
              <p className="byline"><b>04</b>EXL x UCD Data and AI Hackathon 2026, agentic model risk factory</p>
              <h1>Legacy models, re-validated <em>in front of</em> the reviewer.</h1>
              <p className="lead">
                ModelPassport takes a legacy model folder of code, stale documents and data, and produces one evidence
                pack with five stamps. Agents do the work; a human countersigns every stamp under PRA SS1/23.
              </p>
              <div className="actions">
                <Link className="btn btn-solid" to="/dashboard">Open the console</Link>
                <button className="btn" type="button" onClick={rebuild}>Build it again</button>
              </div>
            </div>
            <div className="mock" aria-hidden="true">
              <div className="mock-bar"><span></span><span></span><span></span></div>
              <div className="mock-body">
                <div className="mock-head">
                  <span className="mock-tag">Tier 1 · SAS</span>
                  <h3>Credit scorecard passport</h3>
                  <p>Evidence pack, five stamps, each signed by a person.</p>
                </div>
                <ol className="mock-stamps">
                  {stamps.map((stamp, index) => (
                    <li key={stamp.name}><b>{index + 1}</b>{stamp.name}</li>
                  ))}
                </ol>
                <span className="mock-btn">Sign gate</span>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="problem">
          <div className="wrap">
            <p className="kicker">The problem</p>
            <h2>Model risk work that takes months</h2>
            <p className="intro">A Tier 1 UK retail bank needs current documentation and independent validation for every model it runs. Today the documents are out of date and the queue is long.</p>
            <div className="cards">
              <article className="card"><span className="tag">Estate</span><p className="figure">~250</p><h3>Credit, fraud and pricing models</h3></article>
              <article className="card"><span className="tag">Languages</span><p className="figure">3</p><h3>SAS, R and Python side by side</h3></article>
              <article className="card"><span className="tag">Today</span><p className="figure">8 to 12 weeks</p><h3>For each manual validation</h3></article>
            </div>
          </div>
        </section>

        <section className="section" id="stamps">
          <div className="wrap">
            <p className="kicker">How it works</p>
            <h2>Five stamps, five human gates</h2>
            <p className="intro">Each stage is produced by an agent or a deterministic engine. The next stage cannot start until a reviewer signs.</p>
            <ol className="steps">
              {stamps.map((stamp, index) => (
                <li className="step" key={stamp.name}>
                  <span className="step-num">{index + 1}</span>
                  <div>
                    <h3>{stamp.name}</h3>
                    <p>{stamp.output}</p>
                    <code className="by">{stamp.by}</code>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="section" id="rules">
          <div className="wrap">
            <p className="kicker">Responsible by design</p>
            <h2>The rules every agent follows</h2>
            <div className="promises">
              {rules.map((rule) => (
                <div className="promise" key={rule.title}><h3>{rule.title}</h3><p>{rule.text}</p></div>
              ))}
            </div>
          </div>
        </section>

        <LiveFigures />

        <section className="section">
          <div className="wrap">
            <p className="kicker">Under the hood</p>
            <h2>Four services, one evidence trail</h2>
            <div className="author">
              <div className="monogram" aria-hidden="true">MP</div>
              <div>
                <h3>Only factory_core talks to the browser</h3>
                <p>validation_lab never calls an LLM, so every validation number is reproducible. Services exchange file paths, and every gate decision lands in the audit chain.</p>
                <ul className="services">
                  {services.map((service) => (
                    <li key={service.name}><code>{service.name}</code><span>{service.role}</span></li>
                  ))}
                </ul>
                <div className="author-links">
                  <Link className="main" to="/dashboard">Open the console</Link>
                  <Link to="/models">Browse the inventory</Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="foot">
        <div className="wrap">
          <span>ModelPassport, public and synthetic data only</span>
        </div>
      </footer>
    </div>
  )
}

/** Shows factory figures computed by factory_core, never typed in by hand. */
function LiveFigures() {
  const { data: metrics, isLoading, error } = useFactoryMetrics()
  const modeNote = { mock: 'Sample data, not validation results', live: 'Live from factory_core', snapshot: 'Recorded run' }[apiMode]
  const findings = metrics ? Object.values(metrics.open_findings).reduce((sum, count) => sum + count, 0) : 0

  return (
    <section className="section" id="live">
      <div className="wrap">
        <p className="kicker">From the factory</p>
        <h2>What the agents have produced so far</h2>
        <p className="intro">{modeNote}. Every figure below is computed by the factory, not written by an agent.</p>
        {isLoading && <p className="intro" role="status">Loading figures…</p>}
        {error && <p className="intro">The figures are unavailable right now: {error.message}</p>}
        {metrics && (
          <div className="cards cards-4">
            <article className="card"><span className="tag">Inventory</span><p className="figure">{formatCount(metrics.models_total)}</p><h3>Models discovered</h3></article>
            <article className="card"><span className="tag">Redevelop</span><p className="figure">{formatCount(metrics.parity_certificates_issued)}</p><h3>Parity certificates</h3></article>
            <article className="card"><span className="tag">Validate</span><p className="figure">{formatCount(metrics.validations_completed)}</p><h3>Validations completed</h3></article>
            <article className="card"><span className="tag">Findings</span><p className="figure">{formatCount(findings)}</p><h3>Open findings</h3></article>
          </div>
        )}
      </div>
    </section>
  )
}
