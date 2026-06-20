import { useState, useEffect, useRef } from 'react'
import { traceData } from './data.js'

const IO_BADGES = {
  db_write:      { icon: '🗄️', label: 'DB Write',      color: '#f59e0b' },
  db_read:       { icon: '📖', label: 'DB Read',       color: '#60a5fa' },
  http_call:     { icon: '🌐', label: 'HTTP Call',     color: '#3b82f6' },
  queue_publish: { icon: '📤', label: 'Queue Publish', color: '#10b981' },
  queue_consume: { icon: '📥', label: 'Queue Consume', color: '#34d399' },
  file_write:    { icon: '📁', label: 'File Write',    color: '#fb923c' },
  cache_set:     { icon: '⚡', label: 'Cache Set',     color: '#e879f9' },
}

const TABS = ['Sequence Diagram', 'Trace Timeline', 'Side Effects & Deps']

export default function App() {
  const [activeTab, setActiveTab] = useState('Sequence Diagram')
  const [selectedStep, setSelectedStep] = useState(null)
  const [mermaidReady, setMermaidReady] = useState(false)
  const [copied, setCopied] = useState(false)
  const [showRaw, setShowRaw] = useState(false)
  const diagramRef = useRef(null)

  useEffect(() => {
    const script = document.createElement('script')
    script.type = 'module'
    script.textContent = `
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      window.__mermaid = mermaid;
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        sequence: {
          diagramMarginX: 50, diagramMarginY: 30,
          actorMargin: 60, width: 160, height: 65,
          boxMargin: 10, boxTextMargin: 5,
          noteMargin: 10, messageMargin: 35,
          mirrorActors: false, bottomMarginAdj: 1,
          useMaxWidth: false, rightAngles: false, showSequenceNumbers: true
        },
        themeVariables: {
          primaryColor: '#1a1840',
          primaryTextColor: '#e8e4ff',
          primaryBorderColor: '#6c63ff',
          lineColor: '#4f46cc',
          secondaryColor: '#12103a',
          tertiaryColor: '#0a0820',
          background: '#07071a',
          mainBkg: '#1a1840',
          actorBkg: '#1a1840',
          actorBorder: '#6c63ff',
          actorTextColor: '#e0dcff',
          actorLineColor: '#4f46cc',
          signalColor: '#c4c0e8',
          signalTextColor: '#e0dcff',
          labelBoxBkgColor: '#0d0b2a',
          labelBoxBorderColor: '#6c63ff',
          labelTextColor: '#c4c0e8',
          loopTextColor: '#c4c0e8',
          noteBkgColor: '#1a1840',
          noteBorderColor: '#6c63ff',
          noteTextColor: '#c4c0e8',
          activationBorderColor: '#6c63ff',
          activationBkgColor: '#1a1840',
          sequenceNumberColor: '#fff',
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: '13px'
        }
      });
      window.dispatchEvent(new Event('mermaid-ready'));
    `
    document.head.appendChild(script)
    const handler = () => setMermaidReady(true)
    window.addEventListener('mermaid-ready', handler)
    return () => window.removeEventListener('mermaid-ready', handler)
  }, [])

  useEffect(() => {
    if (!mermaidReady || activeTab !== 'Sequence Diagram' || !diagramRef.current) return
    const render = async () => {
      try {
        diagramRef.current.innerHTML = ''
        const { svg } = await window.__mermaid.render('seq-diagram', traceData.mermaidDiagram)
        diagramRef.current.innerHTML = svg
        const svgEl = diagramRef.current.querySelector('svg')
        if (svgEl) {
          svgEl.style.maxWidth = 'none'
          svgEl.removeAttribute('width')
        }
      } catch (e) {
        diagramRef.current.innerHTML = `<pre style="color:#f87171;font-size:0.8rem;white-space:pre-wrap;font-family:monospace;">Mermaid error: ${e.message}</pre>`
      }
    }
    render()
  }, [mermaidReady, activeTab])

  const copyDiagram = () => {
    navigator.clipboard.writeText(traceData.mermaidDiagram)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const httpSteps = traceData.steps.filter(s => s.ioType === 'http_call').length
  const cacheSteps = traceData.steps.filter(s => s.ioType === 'cache_set').length

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>Flow Trace — {traceData.tracedFlow}</h1>
          <p className="subtitle">
            Repo: <strong>{traceData.repoName}</strong> · polyglot-eval I2 · {new Date(traceData.generatedAt).toLocaleString()}
          </p>
        </div>
        <div className="badges">
          <span className="badge badge-purple">{traceData.steps.length} Steps</span>
          <span className="badge badge-blue">{traceData.externalDeps.length} External Deps</span>
          <span className="badge badge-amber">{traceData.sideEffects.length} Side Effects</span>
        </div>
      </header>

      <div className="tab-bar">
        {TABS.map(t => (
          <button key={t} className={`tab ${activeTab === t ? 'active' : ''}`} onClick={() => setActiveTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <div className="content">
        {activeTab === 'Sequence Diagram' && (
          <div className="diagram-tab">
            <div className="diagram-container" ref={diagramRef}>
              {!mermaidReady && <p className="loading">Loading Mermaid diagram engine…</p>}
            </div>
            <div className="diagram-toolbar">
              <div className="diagram-actions">
                <button className="btn-tool" onClick={() => setShowRaw(!showRaw)}>
                  {showRaw ? '▲ Hide' : '▼ Show'} Source
                </button>
                <button className="btn-tool" onClick={copyDiagram}>
                  {copied ? '✓ Copied' : '📋 Copy Mermaid'}
                </button>
              </div>
              <span className="diagram-hint">
                {traceData.steps.length} steps · {httpSteps} HTTP calls · {cacheSteps} cache ops · scroll to explore
              </span>
            </div>
            {showRaw && <pre className="raw-source">{traceData.mermaidDiagram}</pre>}
          </div>
        )}

        {activeTab === 'Trace Timeline' && (
          <div className="timeline-layout">
            <div className="timeline-scroll">
              <div className="timeline">
                {/* Entry point */}
                <div className="timeline-entry entry-point">
                  <div className="step-circle entry-circle">⬇</div>
                  <div className="step-card entry-card">
                    <div className="entry-label">ENTRY POINT</div>
                    <div className="step-fn">{traceData.entryPoint.function}()</div>
                    <div className="step-file" style={{display:'inline-block',marginBottom:'0.4rem'}}>{traceData.entryPoint.file}:{traceData.entryPoint.line}</div>
                    <div className="step-desc">{traceData.entryPoint.description}</div>
                    <div className="step-registered">Registered as: <code>{traceData.entryPoint.registeredAs}</code></div>
                  </div>
                </div>

                {traceData.steps.map(step => (
                  <div
                    key={step.index}
                    className={`timeline-entry ${selectedStep === step.index ? 'selected' : ''}`}
                    onClick={() => setSelectedStep(selectedStep === step.index ? null : step.index)}
                  >
                    <div className="step-circle">{step.index}</div>
                    <div className="step-card">
                      <div className="step-card-top">
                        <span className="step-file">{step.file.split('/').pop()}:{step.line}</span>
                        {step.ioType && IO_BADGES[step.ioType] && (
                          <span className="io-badge" style={{
                            background: `${IO_BADGES[step.ioType].color}15`,
                            color: IO_BADGES[step.ioType].color,
                            borderColor: `${IO_BADGES[step.ioType].color}40`
                          }}>
                            {IO_BADGES[step.ioType].icon} {IO_BADGES[step.ioType].label}
                          </span>
                        )}
                      </div>
                      <div className="step-fn">{step.function}()</div>
                      <div className="step-desc">{step.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {selectedStep && (() => {
              const s = traceData.steps.find(s => s.index === selectedStep)
              if (!s) return null
              const io = s.ioType && IO_BADGES[s.ioType]
              return (
                <div className="detail-panel">
                  <h3>Step {selectedStep} Details</h3>
                  <div className="detail-row"><span className="detail-label">Function</span><span className="detail-value">{s.function}()</span></div>
                  <div className="detail-row"><span className="detail-label">File</span><span className="detail-value" style={{color:'var(--teal)',fontFamily:'monospace',fontSize:'0.72rem'}}>{s.file}</span></div>
                  <div className="detail-row"><span className="detail-label">Line</span><span className="detail-value">{s.line}</span></div>
                  <div className="detail-row">
                    <span className="detail-label">I/O Type</span>
                    <span className="detail-value">
                      {io ? <span style={{color:io.color}}>{io.icon} {io.label}</span> : <span style={{color:'var(--dim)'}}>None</span>}
                    </span>
                  </div>
                  <div className="detail-row"><span className="detail-label">Description</span><span className="detail-value" style={{fontSize:'0.78rem',color:'var(--muted)'}}>{s.description}</span></div>
                </div>
              )
            })()}
          </div>
        )}

        {activeTab === 'Side Effects & Deps' && (
          <div className="effects-tab">
            <div className="two-columns">
              <div>
                <h3 className="column-title">🌐 External Dependencies ({traceData.externalDeps.length})</h3>
                {traceData.externalDeps.length === 0 ? (
                  <div className="empty-card">No external dependencies detected</div>
                ) : traceData.externalDeps.map((d, i) => (
                  <div className="effect-card" key={i}>
                    <div className="effect-name">{d.name}</div>
                    <div className="effect-source">{d.file.split('/').pop()}:{d.line}</div>
                    <div className="effect-desc">{d.description}</div>
                  </div>
                ))}
              </div>
              <div>
                <h3 className="column-title">⚡ Side Effects ({traceData.sideEffects.length})</h3>
                {traceData.sideEffects.length === 0 ? (
                  <div className="empty-card">No side effects detected</div>
                ) : traceData.sideEffects.map((e, i) => {
                  const io = IO_BADGES[e.type]
                  return (
                    <div className="effect-card" key={i}>
                      <div className="effect-type" style={{color: io ? io.color : 'var(--muted)'}}>
                        {io ? `${io.icon} ${io.label}` : e.type}
                      </div>
                      <div className="effect-source">{e.file.split('/').pop()}:{e.line}</div>
                      <div className="effect-desc">{e.description}</div>
                    </div>
                  )
                })}
              </div>
            </div>

            {traceData.uncertainty.length > 0 && (
              <div className="uncertainty-section">
                <h3>⚠️ Known Uncertainty</h3>
                {traceData.uncertainty.map((u, i) => (
                  <div className="uncertainty-item" key={i}>
                    <span className="uncertainty-file">{u.file.split('/').pop()}:{u.line}</span>
                    <span>{u.description}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
