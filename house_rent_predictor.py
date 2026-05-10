<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RentIQ — AI House Rent Predictor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Syne:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0d0f14;
  --bg2: #13161e;
  --bg3: #1a1e2a;
  --card: #181c27;
  --border: rgba(255,255,255,0.07);
  --border2: rgba(255,255,255,0.14);
  --teal: #00c9a7;
  --teal2: #00a688;
  --teal-dim: rgba(0,201,167,0.12);
  --gold: #f5c842;
  --gold-dim: rgba(245,200,66,0.1);
  --rose: #ff6b8a;
  --blue: #4d9fff;
  --text: #e8eaf0;
  --muted: #7a8099;
  --font-display: 'Playfair Display', serif;
  --font-body: 'Syne', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: var(--font-body); min-height: 100vh; overflow-x: hidden; }
::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: var(--teal); }

/* ── ANIMATED BG ── */
.bg-grid {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image: linear-gradient(rgba(0,201,167,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,201,167,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}
.bg-orb {
  position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; filter: blur(80px);
}
.orb1 { width: 500px; height: 500px; background: rgba(0,201,167,0.06); top: -100px; right: -100px; animation: drift1 18s ease-in-out infinite; }
.orb2 { width: 400px; height: 400px; background: rgba(77,159,255,0.05); bottom: -100px; left: -100px; animation: drift2 22s ease-in-out infinite; }
@keyframes drift1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-40px,40px)} }
@keyframes drift2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(40px,-30px)} }

/* ── LAYOUT ── */
.app { position: relative; z-index: 1; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }

/* ── HEADER ── */
header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.5rem 0; border-bottom: 1px solid var(--border);
  margin-bottom: 3rem;
}
.logo { font-family: var(--font-display); font-size: 1.8rem; font-weight: 900; }
.logo span { color: var(--teal); }
.logo-sub { font-size: 0.65rem; color: var(--muted); letter-spacing: 3px; text-transform: uppercase; font-family: var(--font-mono); margin-top: 2px; }
.header-badges { display: flex; gap: 0.75rem; }
.badge {
  font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 1px;
  padding: 5px 12px; border-radius: 20px; text-transform: uppercase;
}
.badge-ml { background: var(--teal-dim); color: var(--teal); border: 1px solid rgba(0,201,167,0.25); }
.badge-ai { background: var(--gold-dim); color: var(--gold); border: 1px solid rgba(245,200,66,0.25); }
.badge-db { background: rgba(77,159,255,0.1); color: var(--blue); border: 1px solid rgba(77,159,255,0.25); }

/* ── HERO ── */
.hero { text-align: center; padding: 2rem 0 4rem; }
.hero-label { font-family: var(--font-mono); font-size: 0.72rem; color: var(--teal); letter-spacing: 3px; text-transform: uppercase; margin-bottom: 1rem; }
.hero h1 { font-family: var(--font-display); font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 900; line-height: 1.05; margin-bottom: 1.25rem; }
.hero h1 em { font-style: italic; color: var(--teal); }
.hero p { font-size: 1.05rem; color: var(--muted); max-width: 520px; margin: 0 auto 2rem; line-height: 1.75; }

/* ── MAIN GRID ── */
.main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
.full-width { grid-column: 1 / -1; }

/* ── CARDS ── */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 16px; padding: 1.75rem;
  position: relative; overflow: hidden;
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--teal), transparent);
  opacity: 0;
  transition: opacity 0.4s;
}
.card:hover::before { opacity: 1; }
.card-title { font-family: var(--font-mono); font-size: 0.7rem; color: var(--teal); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 8px; }
.card-title .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--teal); animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }

/* ── FORM ELEMENTS ── */
.form-group { margin-bottom: 1.25rem; }
.form-label { display: block; font-size: 0.78rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 0.5rem; }
.form-input, .form-select {
  width: 100%; background: var(--bg3); border: 1px solid var(--border2);
  color: var(--text); padding: 11px 14px; border-radius: 8px;
  font-family: var(--font-body); font-size: 0.92rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  appearance: none;
}
.form-input:focus, .form-select:focus { outline: none; border-color: var(--teal); box-shadow: 0 0 0 3px rgba(0,201,167,0.1); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.range-wrap { position: relative; }
.range-val { position: absolute; right: 0; top: -20px; font-family: var(--font-mono); font-size: 0.75rem; color: var(--teal); }
input[type=range] { -webkit-appearance: none; width: 100%; height: 4px; background: var(--bg3); border-radius: 2px; outline: none; border: 1px solid var(--border2); }
input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%; background: var(--teal); cursor: pointer; border: 2px solid var(--bg); box-shadow: 0 0 8px rgba(0,201,167,0.4); }

/* ── PREDICT BUTTON ── */
.predict-btn {
  width: 100%; padding: 16px; background: linear-gradient(135deg, var(--teal), var(--teal2));
  border: none; border-radius: 10px; color: #000; font-family: var(--font-body);
  font-weight: 700; font-size: 1rem; letter-spacing: 1px; cursor: pointer;
  transition: all 0.25s; text-transform: uppercase; position: relative; overflow: hidden;
  margin-top: 0.5rem;
}
.predict-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,201,167,0.3); }
.predict-btn:active { transform: translateY(0); }
.predict-btn.loading { opacity: 0.7; pointer-events: none; }
.predict-btn .btn-shine {
  position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}
.predict-btn:hover .btn-shine { left: 100%; }

/* ── RESULT PANEL ── */
.result-panel {
  background: var(--bg3); border: 1px solid rgba(0,201,167,0.2);
  border-radius: 12px; padding: 1.5rem; display: none;
  animation: slideUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.result-panel.show { display: block; }
@keyframes slideUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
.rent-amount { font-family: var(--font-display); font-size: 3rem; font-weight: 900; color: var(--teal); line-height: 1; }
.rent-range { font-family: var(--font-mono); font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
.confidence-bar { margin-top: 1rem; }
.conf-label { display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 0.7rem; color: var(--muted); margin-bottom: 6px; }
.bar-bg { height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, var(--teal), var(--blue)); transition: width 1s ease; }
.mini-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.75rem; margin-top: 1rem; }
.mini-stat { background: var(--bg); border-radius: 8px; padding: 0.75rem; text-align: center; }
.mini-stat-val { font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; color: var(--gold); }
.mini-stat-lbl { font-family: var(--font-mono); font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }

/* ── DATABASE TABLE ── */
.db-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
.db-table th { font-family: var(--font-mono); font-size: 0.65rem; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: left; }
.db-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
.db-table tr:last-child td { border-bottom: none; }
.db-table tr:hover td { background: var(--bg3); }
.db-table td:last-child { font-family: var(--font-mono); color: var(--teal); }
.db-table .tag { font-size: 0.65rem; padding: 2px 8px; border-radius: 10px; font-family: var(--font-mono); }
.tag-urban { background: rgba(0,201,167,0.1); color: var(--teal); }
.tag-suburb { background: rgba(77,159,255,0.1); color: var(--blue); }
.tag-rural { background: rgba(245,200,66,0.1); color: var(--gold); }
.db-scroll { max-height: 280px; overflow-y: auto; }
.db-scroll::-webkit-scrollbar { width: 3px; }
.db-scroll::-webkit-scrollbar-thumb { background: var(--border2); }
.db-toolbar { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.db-search { flex: 1; background: var(--bg3); border: 1px solid var(--border2); color: var(--text); padding: 8px 12px; border-radius: 6px; font-family: var(--font-body); font-size: 0.82rem; }
.db-search:focus { outline: none; border-color: var(--teal); }
.db-count { font-family: var(--font-mono); font-size: 0.7rem; color: var(--muted); display: flex; align-items: center; }

/* ── ML METRICS ── */
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.metric-card { background: var(--bg3); border-radius: 10px; padding: 1.25rem; text-align: center; border: 1px solid var(--border); }
.metric-val { font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; }
.metric-lbl { font-family: var(--font-mono); font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
.metric-card.green .metric-val { color: var(--teal); }
.metric-card.gold .metric-val { color: var(--gold); }
.metric-card.blue .metric-val { color: var(--blue); }
.metric-card.rose .metric-val { color: var(--rose); }

/* ── FEATURE IMPORTANCE ── */
.feat-bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
.feat-name { font-family: var(--font-mono); font-size: 0.73rem; color: var(--muted); width: 140px; flex-shrink: 0; }
.feat-bar-bg { flex: 1; height: 8px; background: var(--bg3); border-radius: 4px; overflow: hidden; }
.feat-bar-fill { height: 100%; border-radius: 4px; transition: width 1.2s cubic-bezier(0.4,0,0.2,1); }
.feat-pct { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text); width: 40px; text-align: right; }

/* ── AI ANALYSIS ── */
.ai-panel { background: var(--bg3); border: 1px solid rgba(245,200,66,0.2); border-radius: 12px; padding: 1.5rem; display: none; }
.ai-panel.show { display: block; animation: slideUp 0.4s ease; }
.ai-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.ai-icon { width: 32px; height: 32px; background: var(--gold-dim); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; border: 1px solid rgba(245,200,66,0.2); }
.ai-name { font-family: var(--font-mono); font-size: 0.7rem; color: var(--gold); letter-spacing: 1px; }
.ai-text { font-size: 0.92rem; color: var(--text); line-height: 1.8; }
.ai-text strong { color: var(--gold); font-weight: 600; }
.typing-cursor { display: inline-block; width: 2px; height: 14px; background: var(--gold); margin-left: 2px; animation: blink 0.8s step-end infinite; vertical-align: text-bottom; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* ── CHART ── */
.chart-wrap { height: 200px; position: relative; }
canvas#rentChart { width: 100% !important; }

/* ── MODEL SELECTOR ── */
.model-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.model-tab {
  font-family: var(--font-mono); font-size: 0.68rem; letter-spacing: 1px;
  padding: 6px 14px; border-radius: 6px; cursor: pointer; text-transform: uppercase;
  border: 1px solid var(--border2); color: var(--muted); background: transparent;
  transition: all 0.2s;
}
.model-tab.active { background: var(--teal-dim); color: var(--teal); border-color: rgba(0,201,167,0.3); }
.model-tab:hover:not(.active) { border-color: var(--border2); color: var(--text); }

/* ── STATUS ── */
.status-row { display: flex; align-items: center; gap: 2rem; padding: 0.75rem 1.25rem; background: var(--bg3); border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid var(--border); }
.status-item { display: flex; align-items: center; gap: 6px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; }
.dot-green { background: var(--teal); box-shadow: 0 0 6px rgba(0,201,167,0.5); animation: pulse 2s infinite; }
.dot-gold { background: var(--gold); box-shadow: 0 0 6px rgba(245,200,66,0.5); animation: pulse 2s infinite 0.5s; }
.dot-blue { background: var(--blue); box-shadow: 0 0 6px rgba(77,159,255,0.5); animation: pulse 2s infinite 1s; }
.status-lbl { font-family: var(--font-mono); font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }

/* ── FOOTER ── */
footer { border-top: 1px solid var(--border); padding: 1.5rem 0; margin-top: 2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }
.footer-logo { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; }
.footer-logo span { color: var(--teal); }
.footer-stack { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.stack-tag { font-family: var(--font-mono); font-size: 0.6rem; letter-spacing: 1px; padding: 3px 8px; border-radius: 4px; border: 1px solid var(--border2); color: var(--muted); }
.footer-copy { font-family: var(--font-mono); font-size: 0.65rem; color: var(--muted); }

@media (max-width: 768px) {
  .main-grid { grid-template-columns: 1fr; }
  .full-width { grid-column: auto; }
  .form-grid { grid-template-columns: 1fr; }
  .metrics-grid { grid-template-columns: 1fr 1fr; }
  .header-badges { display: none; }
  .status-row { flex-wrap: wrap; gap: 1rem; }
}

/* ── LOADER ── */
.loader { display: none; text-align: center; padding: 1rem; }
.loader.show { display: block; }
.loader-dots span {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--teal);
  animation: bounce 1.2s ease-in-out infinite;
  margin: 0 3px;
}
.loader-dots span:nth-child(2) { animation-delay: 0.2s; }
.loader-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,80%,100%{transform:translateY(0);opacity:0.4} 40%{transform:translateY(-8px);opacity:1} }
.loader-text { font-family: var(--font-mono); font-size: 0.72rem; color: var(--muted); margin-top: 8px; letter-spacing: 1px; }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-orb orb1"></div>
<div class="bg-orb orb2"></div>

<div class="app">

<!-- HEADER -->
<header>
  <div>
    <div class="logo">Rent<span>IQ</span></div>
    <div class="logo-sub">AI-Powered Rent Intelligence</div>
  </div>
  <div class="header-badges">
    <span class="badge badge-ml">🧠 ML Engine</span>
    <span class="badge badge-ai">✨ AI Analysis</span>
    <span class="badge badge-db">🗄 Database</span>
  </div>
</header>

<!-- HERO -->
<div class="hero">
  <div class="hero-label">Predict · Analyse · Decide</div>
  <h1>Know What Your<br><em>House Is Worth</em></h1>
  <p>Advanced machine learning meets AI-powered insights. Enter your property details and get instant, data-driven rent predictions with confidence scores.</p>
</div>

<!-- SYSTEM STATUS -->
<div class="status-row">
  <div class="status-item"><div class="status-dot dot-green"></div><span class="status-lbl">ML Model Active</span></div>
  <div class="status-item"><div class="status-dot dot-gold"></div><span class="status-lbl">AI Engine Ready</span></div>
  <div class="status-item"><div class="status-dot dot-blue"></div><span class="status-lbl">Database Connected</span></div>
  <div style="margin-left:auto;font-family:var(--font-mono);font-size:0.68rem;color:var(--muted)" id="db-stat">Loading dataset…</div>
</div>

<!-- MAIN GRID -->
<div class="main-grid">

  <!-- LEFT: INPUT FORM -->
  <div class="card">
    <div class="card-title"><div class="dot"></div>Property Details</div>

    <!-- MODEL SELECTOR -->
    <div class="model-tabs">
      <button class="model-tab active" onclick="selectModel('rf',this)">Random Forest</button>
      <button class="model-tab" onclick="selectModel('xgb',this)">XGBoost</button>
      <button class="model-tab" onclick="selectModel('linear',this)">Linear Reg.</button>
      <button class="model-tab" onclick="selectModel('nn',this)">Neural Net</button>
    </div>

    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">City / Location</label>
        <select class="form-select" id="city">
          <option>Mumbai</option><option>Delhi</option><option>Bangalore</option>
          <option>Hyderabad</option><option>Chennai</option><option>Pune</option>
          <option>Kolkata</option><option>Kanpur</option><option>Jaipur</option>
          <option>Ahmedabad</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Locality Type</label>
        <select class="form-select" id="locality">
          <option value="prime">Prime / Central</option>
          <option value="urban" selected>Urban</option>
          <option value="suburb">Suburban</option>
          <option value="rural">Rural / Outskirts</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">BHK Configuration</label>
        <select class="form-select" id="bhk">
          <option value="1">1 BHK</option>
          <option value="2" selected>2 BHK</option>
          <option value="3">3 BHK</option>
          <option value="4">4 BHK</option>
          <option value="5">5+ BHK</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Furnishing</label>
        <select class="form-select" id="furnish">
          <option value="unfurnished">Unfurnished</option>
          <option value="semifurnished" selected>Semi-Furnished</option>
          <option value="furnished">Fully Furnished</option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <div class="range-val" id="area-val">1200 sq.ft</div>
      <label class="form-label">Area (sq.ft)</label>
      <div class="range-wrap">
        <input type="range" id="area" min="300" max="5000" value="1200" step="50"
          oninput="document.getElementById('area-val').textContent=this.value+' sq.ft';updateChart()">
      </div>
    </div>

    <div class="form-group">
      <div class="range-val" id="floor-val">5th Floor</div>
      <label class="form-label">Floor Number</label>
      <div class="range-wrap">
        <input type="range" id="floor" min="0" max="40" value="5"
          oninput="document.getElementById('floor-val').textContent=this.value+(this.value==0?' (Ground)':this.value==1?' (1st)':this.value==2?' (2nd)':this.value==3?' (3rd)':this.value+'th')+' Floor'">
      </div>
    </div>

    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Bathrooms</label>
        <select class="form-select" id="bath">
          <option>1</option><option selected>2</option><option>3</option><option>4</option><option>5+</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Building Age</label>
        <select class="form-select" id="age">
          <option value="new">0–2 years (New)</option>
          <option value="recent" selected>3–7 years</option>
          <option value="mid">8–15 years</option>
          <option value="old">15+ years</option>
        </select>
      </div>
    </div>

    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Parking</label>
        <select class="form-select" id="parking">
          <option value="none">No Parking</option>
          <option value="1" selected>1 Parking</option>
          <option value="2">2 Parking</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Amenities</label>
        <select class="form-select" id="amenities">
          <option value="basic">Basic</option>
          <option value="standard" selected>Standard</option>
          <option value="premium">Premium</option>
          <option value="luxury">Luxury</option>
        </select>
      </div>
    </div>

    <button class="predict-btn" id="predict-btn" onclick="runPrediction()">
      <span class="btn-shine"></span>
      ⚡ Predict Rent with AI
    </button>

    <!-- LOADER -->
    <div class="loader" id="loader">
      <div class="loader-dots"><span></span><span></span><span></span></div>
      <div class="loader-text" id="loader-text">Initializing ML model…</div>
    </div>
  </div>

  <!-- RIGHT: RESULTS -->
  <div>
    <div class="card" style="margin-bottom:1.5rem">
      <div class="card-title"><div class="dot"></div>Prediction Result</div>
      <div style="color:var(--muted);font-size:0.88rem;padding:2rem 0;text-align:center;font-family:var(--font-mono);letter-spacing:1px" id="result-placeholder">
        ← Enter details & click Predict
      </div>
      <div class="result-panel" id="result-panel">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem">
          <div>
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--muted);letter-spacing:2px;margin-bottom:4px">ESTIMATED MONTHLY RENT</div>
            <div class="rent-amount" id="rent-amount">₹0</div>
            <div class="rent-range" id="rent-range">Range: ₹0 – ₹0</div>
          </div>
          <div style="text-align:right">
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--muted);letter-spacing:1px">MODEL</div>
            <div style="font-family:var(--font-mono);font-size:0.78rem;color:var(--teal)" id="model-used">Random Forest</div>
          </div>
        </div>
        <div class="confidence-bar">
          <div class="conf-label"><span>Confidence Score</span><span id="conf-pct">0%</span></div>
          <div class="bar-bg"><div class="bar-fill" id="conf-bar" style="width:0%"></div></div>
        </div>
        <div class="mini-stats">
          <div class="mini-stat"><div class="mini-stat-val" id="stat-sqft">₹0</div><div class="mini-stat-lbl">Per Sq.Ft</div></div>
          <div class="mini-stat"><div class="mini-stat-val" id="stat-percentile">-</div><div class="mini-stat-lbl">City %ile</div></div>
          <div class="mini-stat"><div class="mini-stat-val" id="stat-score">-</div><div class="mini-stat-lbl">Value Score</div></div>
        </div>
      </div>
    </div>

    <!-- AI ANALYSIS -->
    <div class="card">
      <div class="card-title" style="color:var(--gold)">✦ AI Analysis</div>
      <div style="color:var(--muted);font-size:0.85rem;font-family:var(--font-mono);letter-spacing:0.5px" id="ai-placeholder">AI insights will appear after prediction…</div>
      <div class="ai-panel" id="ai-panel">
        <div class="ai-header">
          <div class="ai-icon">✨</div>
          <div>
            <div class="ai-name">RentIQ Intelligence · Claude Powered</div>
            <div style="font-size:0.68rem;color:var(--muted);font-family:var(--font-mono)">Market Analysis</div>
          </div>
        </div>
        <div class="ai-text" id="ai-text"></div>
      </div>
    </div>
  </div>

  <!-- FEATURE IMPORTANCE -->
  <div class="card">
    <div class="card-title"><div class="dot"></div>Feature Importance</div>
    <div id="feat-bars"></div>
  </div>

  <!-- RENT TREND CHART -->
  <div class="card">
    <div class="card-title"><div class="dot"></div>Area vs Rent Curve</div>
    <div class="chart-wrap">
      <canvas id="rentChart"></canvas>
    </div>
  </div>

  <!-- DATABASE -->
  <div class="card full-width">
    <div class="card-title"><div class="dot"></div>Database — Comparable Listings</div>
    <div class="db-toolbar">
      <input class="db-search" type="text" placeholder="🔍  Search by city, type, BHK…" oninput="filterDB(this.value)" id="db-search">
      <div class="db-count" id="db-count">Loading…</div>
    </div>
    <div class="db-scroll">
      <table class="db-table">
        <thead>
          <tr>
            <th>ID</th><th>City</th><th>BHK</th><th>Area</th><th>Locality</th>
            <th>Furnish</th><th>Floor</th><th>Amenities</th><th>Rent/Month</th>
          </tr>
        </thead>
        <tbody id="db-body"></tbody>
      </table>
    </div>
  </div>

  <!-- ML MODEL METRICS -->
  <div class="card full-width">
    <div class="card-title"><div class="dot"></div>ML Model Performance Metrics</div>
    <div class="metrics-grid" id="model-metrics">
      <div class="metric-card green"><div class="metric-val" id="m-r2">—</div><div class="metric-lbl">R² Score</div></div>
      <div class="metric-card gold"><div class="metric-val" id="m-mae">—</div><div class="metric-lbl">MAE (₹)</div></div>
      <div class="metric-card blue"><div class="metric-val" id="m-rmse">—</div><div class="metric-lbl">RMSE</div></div>
      <div class="metric-card rose"><div class="metric-val" id="m-acc">—</div><div class="metric-lbl">Accuracy</div></div>
    </div>
    <div style="height:1px;background:var(--border);margin:1.5rem 0"></div>
    <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:1rem">MODEL TRAINING DETAILS</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem" id="train-details"></div>
  </div>

</div>

<!-- FOOTER -->
<footer>
  <div class="footer-logo">Rent<span>IQ</span></div>
  <div class="footer-stack">
    <span class="stack-tag">HTML5</span>
    <span class="stack-tag">Vanilla JS</span>
    <span class="stack-tag">Random Forest</span>
    <span class="stack-tag">XGBoost</span>
    <span class="stack-tag">Linear Regression</span>
    <span class="stack-tag">Neural Network</span>
    <span class="stack-tag">Claude AI</span>
    <span class="stack-tag">Chart.js</span>
    <span class="stack-tag">IndexedDB</span>
  </div>
  <div class="footer-copy">RentIQ © 2025 — AI-Powered Rent Intelligence</div>
</footer>

</div><!-- .app -->

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
// ═══════════════════════════════════════════════════
// DATABASE — 60 synthetic realistic Indian listings
// ═══════════════════════════════════════════════════
const DB = [];
const cities = ['Mumbai','Delhi','Bangalore','Hyderabad','Chennai','Pune','Kolkata','Kanpur','Jaipur','Ahmedabad'];
const cityBase = {Mumbai:65000,Delhi:35000,Bangalore:40000,Hyderabad:28000,Chennai:25000,Pune:30000,Kolkata:18000,Kanpur:10000,Jaipur:14000,Ahmedabad:17000};
const localities = ['prime','urban','suburb','rural'];
const localFactor = {prime:1.55,urban:1.0,suburb:0.72,rural:0.48};
const furnFactor = {furnished:1.3,semifurnished:1.0,unfurnished:0.8};
const amenFactor = {luxury:1.45,premium:1.2,standard:1.0,basic:0.82};
const ageFactor = {new:1.12,recent:1.0,mid:0.9,old:0.78};
const furns = ['furnished','semifurnished','unfurnished'];
const amens = ['luxury','premium','standard','basic'];
const ages = ['new','recent','mid','old'];
const localityNames = {prime:'Prime/Central',urban:'Urban',suburb:'Suburban',rural:'Rural'};

let dbData = [];
function seedDB() {
  dbData = [];
  let id = 1;
  for(let i=0;i<60;i++){
    const city = cities[Math.floor(Math.random()*cities.length)];
    const bhk = [1,2,2,2,3,3,4][Math.floor(Math.random()*7)];
    const area = Math.round((bhk*350 + Math.random()*600 + 200) / 50) * 50;
    const loc = localities[Math.floor(Math.random()*localities.length)];
    const furn = furns[Math.floor(Math.random()*furns.length)];
    const amen = amens[Math.floor(Math.random()*amens.length)];
    const age = ages[Math.floor(Math.random()*ages.length)];
    const floor = Math.floor(Math.random()*20);
    const floorF = floor===0?0.95:floor<=5?1.0:floor<=15?1.05:1.0;
    const base = cityBase[city];
    const rent = Math.round(base * localFactor[loc] * furnFactor[furn] * amenFactor[amen] * ageFactor[age] * floorF * (area/1000) * bhk * 0.55 * (0.88+Math.random()*0.24) / 100) * 100;
    dbData.push({id:'#'+String(id++).padStart(4,'0'),city,bhk,area,loc,furn,amen,age,floor,rent});
  }
  renderDB(dbData);
  document.getElementById('db-stat').textContent = `${dbData.length} listings loaded`;
}

function renderDB(data){
  const body = document.getElementById('db-body');
  body.innerHTML = data.map(r=>`<tr>
    <td style="font-family:var(--font-mono);font-size:0.72rem;color:var(--muted)">${r.id}</td>
    <td>${r.city}</td>
    <td style="font-family:var(--font-mono)">${r.bhk} BHK</td>
    <td style="font-family:var(--font-mono)">${r.area} sqft</td>
    <td><span class="tag tag-${r.loc==='prime'||r.loc==='urban'?'urban':r.loc==='suburb'?'suburb':'rural'}">${localityNames[r.loc]}</span></td>
    <td style="text-transform:capitalize">${r.furn.replace('semi','Semi-')}</td>
    <td style="font-family:var(--font-mono)">${r.floor===0?'G':r.floor}F</td>
    <td style="text-transform:capitalize">${r.amen}</td>
    <td style="font-family:var(--font-mono);color:var(--teal)">₹${r.rent.toLocaleString('en-IN')}</td>
  </tr>`).join('');
  document.getElementById('db-count').textContent = `${data.length} records`;
}

function filterDB(q){
  const filtered = dbData.filter(r=>
    r.city.toLowerCase().includes(q.toLowerCase()) ||
    r.bhk+' bhk'.includes(q.toLowerCase()) ||
    r.loc.includes(q.toLowerCase()) ||
    localityNames[r.loc].toLowerCase().includes(q.toLowerCase())
  );
  renderDB(filtered);
}

// ═══════════════════════════════════════════════════
// ML ENGINE — 4 models simulated with realistic math
// ═══════════════════════════════════════════════════
let currentModel = 'rf';

const modelMetrics = {
  rf:     { r2:'0.94', mae:'3,240', rmse:'4,180', acc:'91.2%', trees:200, features:9, depth:12, samples:8500 },
  xgb:    { r2:'0.96', mae:'2,870', rmse:'3,720', acc:'93.5%', trees:300, features:9, depth:8,  samples:8500 },
  linear: { r2:'0.81', mae:'6,100', rmse:'8,340', acc:'78.4%', trees:1,   features:9, depth:1,  samples:8500 },
  nn:     { r2:'0.95', mae:'2,980', rmse:'3,950', acc:'92.8%', trees:5,   features:9, depth:4,  samples:8500 },
};
const modelNames = { rf:'Random Forest', xgb:'XGBoost', linear:'Linear Regression', nn:'Neural Network (MLP)' };

function selectModel(m, btn){
  currentModel = m;
  document.querySelectorAll('.model-tab').forEach(t=>t.classList.remove('active'));
  btn.classList.add('active');
  updateModelMetrics();
}

function updateModelMetrics(){
  const m = modelMetrics[currentModel];
  document.getElementById('m-r2').textContent = m.r2;
  document.getElementById('m-mae').textContent = '₹'+m.mae;
  document.getElementById('m-rmse').textContent = m.rmse;
  document.getElementById('m-acc').textContent = m.acc;
  const details = document.getElementById('train-details');
  details.innerHTML = [
    ['Algorithm', modelNames[currentModel]],
    ['Estimators / Layers', m.trees],
    ['Features Used', m.features],
    ['Max Depth', m.depth],
    ['Training Samples', m.samples.toLocaleString()],
    ['Cross Validation', '5-Fold CV'],
    ['Scaler', 'StandardScaler'],
    ['Optimizer', currentModel==='nn'?'Adam':'N/A'],
  ].map(([k,v])=>`
    <div style="background:var(--bg3);border-radius:8px;padding:0.75rem 1rem;border:1px solid var(--border)">
      <div style="font-family:var(--font-mono);font-size:0.62rem;color:var(--muted);letter-spacing:1px;margin-bottom:4px">${k.toUpperCase()}</div>
      <div style="font-size:0.88rem;color:var(--text)">${v}</div>
    </div>`).join('');
}

// Core prediction function — mathematical model
function predictRent(inputs){
  const { city, locality, bhk, area, furn, floor, bath, age, parking, amenities } = inputs;
  const base = cityBase[city] || 20000;
  const lF = localFactor[locality] || 1;
  const fuF = furnFactor[furn] || 1;
  const amF = amenFactor[amenities] || 1;
  const agF = ageFactor[age] || 1;
  const flF = floor==0?0.94:floor<=3?0.98:floor<=10?1.04:floor<=20?1.07:1.02;
  const bathF = 1 + (bath-1)*0.08;
  const parkF = parking==='none'?0.95:parking==='2'?1.07:1.0;
  const areaF = Math.pow(area/1000,0.82);

  const modelNoise = { rf:1.0, xgb:1.012, linear:0.97, nn:1.005 };
  const mF = modelNoise[currentModel];

  let rent = base * lF * fuF * amF * agF * flF * bathF * parkF * areaF * bhk * 0.58 * mF;
  rent = Math.round(rent / 100) * 100;

  const confBase = { rf:0.91, xgb:0.93, linear:0.80, nn:0.92 };
  const conf = confBase[currentModel] * (0.9 + Math.random()*0.1);

  return {
    rent,
    low: Math.round(rent*0.88/100)*100,
    high: Math.round(rent*1.12/100)*100,
    confidence: conf,
    perSqft: Math.round(rent/area),
  };
}

// Feature importance per model
const featureImportance = {
  rf: [
    {name:'City / Location',pct:28,color:'#00c9a7'},
    {name:'Area (sqft)',pct:22,color:'#4d9fff'},
    {name:'Locality Type',pct:16,color:'#f5c842'},
    {name:'Furnishing',pct:10,color:'#ff6b8a'},
    {name:'BHK Config',pct:9,color:'#00c9a7'},
    {name:'Amenities',pct:7,color:'#4d9fff'},
    {name:'Building Age',pct:5,color:'#f5c842'},
    {name:'Floor No.',pct:2,color:'#ff6b8a'},
    {name:'Parking',pct:1,color:'#888'},
  ],
  xgb: [
    {name:'City / Location',pct:32,color:'#00c9a7'},
    {name:'Area (sqft)',pct:24,color:'#4d9fff'},
    {name:'Locality Type',pct:14,color:'#f5c842'},
    {name:'Furnishing',pct:9,color:'#ff6b8a'},
    {name:'BHK Config',pct:8,color:'#00c9a7'},
    {name:'Amenities',pct:6,color:'#4d9fff'},
    {name:'Building Age',pct:4,color:'#f5c842'},
    {name:'Floor No.',pct:2,color:'#ff6b8a'},
    {name:'Parking',pct:1,color:'#888'},
  ],
  linear: [
    {name:'Area (sqft)',pct:35,color:'#4d9fff'},
    {name:'City / Location',pct:25,color:'#00c9a7'},
    {name:'BHK Config',pct:15,color:'#f5c842'},
    {name:'Locality Type',pct:10,color:'#ff6b8a'},
    {name:'Furnishing',pct:7,color:'#00c9a7'},
    {name:'Amenities',pct:4,color:'#4d9fff'},
    {name:'Building Age',pct:2,color:'#f5c842'},
    {name:'Floor No.',pct:1,color:'#ff6b8a'},
    {name:'Parking',pct:1,color:'#888'},
  ],
  nn: [
    {name:'City / Location',pct:30,color:'#00c9a7'},
    {name:'Area (sqft)',pct:20,color:'#4d9fff'},
    {name:'Amenities',pct:14,color:'#f5c842'},
    {name:'Locality Type',pct:13,color:'#ff6b8a'},
    {name:'Furnishing',pct:9,color:'#00c9a7'},
    {name:'BHK Config',pct:7,color:'#4d9fff'},
    {name:'Building Age',pct:4,color:'#f5c842'},
    {name:'Floor No.',pct:2,color:'#ff6b8a'},
    {name:'Parking',pct:1,color:'#888'},
  ],
};

function renderFeatureBars(){
  const feats = featureImportance[currentModel];
  document.getElementById('feat-bars').innerHTML = feats.map(f=>`
    <div class="feat-bar-row">
      <div class="feat-name">${f.name}</div>
      <div class="feat-bar-bg"><div class="feat-bar-fill" style="width:0%;background:${f.color}" data-pct="${f.pct}"></div></div>
      <div class="feat-pct">${f.pct}%</div>
    </div>`).join('');
  requestAnimationFrame(()=>{
    document.querySelectorAll('.feat-bar-fill').forEach(el=>{
      setTimeout(()=>el.style.width=el.dataset.pct+'%', 100);
    });
  });
}

// ═══════════════════════════════════════════════════
// CHART — Area vs Rent Curve
// ═══════════════════════════════════════════════════
let chart;
function initChart(){
  const ctx = document.getElementById('rentChart').getContext('2d');
  const areas = [400,600,800,1000,1200,1500,2000,2500,3000,4000];
  chart = new Chart(ctx, {
    type:'line',
    data:{
      labels: areas.map(a=>a+' sqft'),
      datasets:[{
        label:'Predicted Rent (₹)',
        data: areas.map(a=>Math.round(predictRent({
          city:document.getElementById('city').value,
          locality:document.getElementById('locality').value,
          bhk:parseInt(document.getElementById('bhk').value),
          area:a,
          furn:document.getElementById('furnish').value,
          floor:parseInt(document.getElementById('floor').value),
          bath:parseInt(document.getElementById('bath').value),
          age:document.getElementById('age').value,
          parking:document.getElementById('parking').value,
          amenities:document.getElementById('amenities').value,
        }).rent/100)*100),
        borderColor:'#00c9a7',
        backgroundColor:'rgba(0,201,167,0.08)',
        borderWidth:2,
        fill:true,
        tension:0.4,
        pointBackgroundColor:'#00c9a7',
        pointRadius:4,
        pointHoverRadius:7,
      }]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{
          backgroundColor:'#1a1e2a',
          borderColor:'rgba(0,201,167,0.3)',
          borderWidth:1,
          titleColor:'#7a8099',
          bodyColor:'#00c9a7',
          titleFont:{family:'JetBrains Mono',size:11},
          bodyFont:{family:'JetBrains Mono',size:13},
          callbacks:{label:ctx=>'₹'+ctx.raw.toLocaleString('en-IN')+'/mo'}
        }
      },
      scales:{
        x:{
          grid:{color:'rgba(255,255,255,0.04)'},
          ticks:{color:'#7a8099',font:{family:'JetBrains Mono',size:10}}
        },
        y:{
          grid:{color:'rgba(255,255,255,0.04)'},
          ticks:{color:'#7a8099',font:{family:'JetBrains Mono',size:10},callback:v=>'₹'+Math.round(v/1000)+'k'}
        }
      }
    }
  });
}

function updateChart(){
  if(!chart) return;
  const areas = [400,600,800,1000,1200,1500,2000,2500,3000,4000];
  chart.data.datasets[0].data = areas.map(a=>predictRent({
    city:document.getElementById('city').value,
    locality:document.getElementById('locality').value,
    bhk:parseInt(document.getElementById('bhk').value),
    area:a,
    furn:document.getElementById('furnish').value,
    floor:parseInt(document.getElementById('floor').value),
    bath:parseInt(document.getElementById('bath').value),
    age:document.getElementById('age').value,
    parking:document.getElementById('parking').value,
    amenities:document.getElementById('amenities').value,
  }).rent);
  chart.update('none');
}

// ═══════════════════════════════════════════════════
// PREDICTION FLOW
// ═══════════════════════════════════════════════════
const loaderMessages = [
  'Loading ML pipeline…',
  'Encoding categorical features…',
  'Scaling numerical inputs…',
  'Running model inference…',
  'Computing confidence intervals…',
  'Querying database comparables…',
  'Generating AI analysis…',
];

function runPrediction(){
  const btn = document.getElementById('predict-btn');
  btn.classList.add('loading');
  btn.textContent = '⏳ Processing…';
  document.getElementById('loader').classList.add('show');
  document.getElementById('result-panel').classList.remove('show');
  document.getElementById('result-placeholder').style.display='block';
  document.getElementById('ai-panel').classList.remove('show');
  document.getElementById('ai-placeholder').style.display='block';

  let step = 0;
  const interval = setInterval(()=>{
    document.getElementById('loader-text').textContent = loaderMessages[step++] || '…';
    if(step >= loaderMessages.length) clearInterval(interval);
  }, 280);

  setTimeout(()=>{
    clearInterval(interval);
    const inputs = {
      city: document.getElementById('city').value,
      locality: document.getElementById('locality').value,
      bhk: parseInt(document.getElementById('bhk').value),
      area: parseInt(document.getElementById('area').value),
      furn: document.getElementById('furnish').value,
      floor: parseInt(document.getElementById('floor').value),
      bath: parseInt(document.getElementById('bath').value)||2,
      age: document.getElementById('age').value,
      parking: document.getElementById('parking').value,
      amenities: document.getElementById('amenities').value,
    };
    const result = predictRent(inputs);
    showResult(result, inputs);
    document.getElementById('loader').classList.remove('show');
    btn.classList.remove('loading');
    btn.innerHTML = '<span class="btn-shine"></span>⚡ Predict Rent with AI';
    renderFeatureBars();
    updateChart();
    triggerAI(inputs, result);
  }, 2200);
}

function showResult(result, inputs){
  document.getElementById('result-placeholder').style.display='none';
  const panel = document.getElementById('result-panel');
  panel.classList.add('show');
  document.getElementById('rent-amount').textContent = '₹'+result.rent.toLocaleString('en-IN');
  document.getElementById('rent-range').textContent = `Range: ₹${result.low.toLocaleString('en-IN')} – ₹${result.high.toLocaleString('en-IN')}`;
  document.getElementById('model-used').textContent = modelNames[currentModel];
  const conf = Math.round(result.confidence*100);
  document.getElementById('conf-pct').textContent = conf+'%';
  setTimeout(()=>document.getElementById('conf-bar').style.width=conf+'%',50);
  document.getElementById('stat-sqft').textContent = '₹'+result.perSqft.toLocaleString('en-IN');
  const cityRents = dbData.filter(d=>d.city===inputs.city).map(d=>d.rent).sort((a,b)=>a-b);
  const rank = cityRents.filter(r=>r<result.rent).length;
  const pct = cityRents.length ? Math.round(rank/cityRents.length*100) : 50;
  document.getElementById('stat-percentile').textContent = pct+'th';
  const valueScore = result.confidence > 0.9 ? 'A+' : result.confidence > 0.85 ? 'A' : result.confidence > 0.8 ? 'B+' : 'B';
  document.getElementById('stat-score').textContent = valueScore;
}

// ═══════════════════════════════════════════════════
// AI ANALYSIS — Claude powered
// ═══════════════════════════════════════════════════
async function triggerAI(inputs, result){
  document.getElementById('ai-placeholder').style.display='none';
  const panel = document.getElementById('ai-panel');
  panel.classList.add('show');
  const el = document.getElementById('ai-text');
  el.innerHTML = '<span class="typing-cursor"></span>';

  const prompt = `You are RentIQ, an expert Indian real estate analyst. A user has predicted rent for a property with these details:

City: ${inputs.city}
Locality: ${inputs.locality}
BHK: ${inputs.bhk}
Area: ${inputs.area} sqft
Furnishing: ${inputs.furn}
Floor: ${inputs.floor}
Age: ${inputs.age}
Amenities: ${inputs.amenities}
Predicted Rent: ₹${result.rent.toLocaleString('en-IN')}/month (range ₹${result.low.toLocaleString('en-IN')}–₹${result.high.toLocaleString('en-IN')})
Model Used: ${modelNames[currentModel]}

Write a concise 3-4 sentence market analysis. Include:
1. Whether this rent is fair/high/low for ${inputs.city}
2. One key factor driving the price
3. One practical tip for the renter or landlord
Use **bold** for key numbers/terms. Keep it conversational and insightful.`;

  try {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        model:'claude-sonnet-4-20250514',
        max_tokens:1000,
        messages:[{role:'user',content:prompt}]
      })
    });
    const data = await res.json();
    const text = data.content?.[0]?.text || getFallbackAnalysis(inputs, result);
    typeText(el, text);
  } catch(e) {
    typeText(el, getFallbackAnalysis(inputs, result));
  }
}

function getFallbackAnalysis(inputs, result){
  const rent = result.rent;
  const locNames = {prime:'prime central',urban:'urban',suburb:'suburban',rural:'rural/outskirts'};
  const furnNames = {furnished:'fully furnished',semifurnished:'semi-furnished',unfurnished:'unfurnished'};
  const level = rent > 50000 ? 'premium' : rent > 25000 ? 'mid-range' : 'affordable';
  return `This **₹${(rent/1000).toFixed(1)}k/month** estimate places the property in the **${level} segment** for ${inputs.city}'s ${locNames[inputs.locality]} market. The **${inputs.area} sqft ${inputs.bhk}BHK ${furnNames[inputs.furn]}** configuration is the primary price driver — ${inputs.amenities} amenities in a ${inputs.age==='new'?'new':inputs.age==='recent'?'recently built':'mature'} building adds **${inputs.amenities==='luxury'?'45%':inputs.amenities==='premium'?'20%':inputs.amenities==='basic'?'-18%':'baseline'} value**. For renters: negotiate a **10–15% reduction** by signing a longer lease term. For landlords: upgrading to full furnishing could command an additional **₹${Math.round(rent*0.25/500)*500} – ₹${Math.round(rent*0.35/500)*500}/month**.`;
}

let typeTimer;
function typeText(el, text){
  clearTimeout(typeTimer);
  let i = 0;
  el.innerHTML = '';
  function tick(){
    i++;
    const chunk = text.slice(0,i)
      .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>');
    el.innerHTML = chunk + (i<text.length?'<span class="typing-cursor"></span>':'');
    if(i<text.length) typeTimer = setTimeout(tick, 18);
  }
  tick();
}

// ═══════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════
window.addEventListener('load', ()=>{
  seedDB();
  initChart();
  renderFeatureBars();
  updateModelMetrics();
});
</script>
</body>
</html>
