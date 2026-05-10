import { useState, useEffect, useRef, useCallback } from "react";

// ─── Utility helpers ───────────────────────────────────────────────
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fmt = (n) => "₹" + Number(n).toLocaleString("en-IN");
const rnd = (n, d = 0) => Number(n).toFixed(d);

// ─── Synthetic ML model (deterministic Random-Forest-like logic) ───
function predictRent(inputs) {
  const {
    city, area, bhk, bathrooms, furnishing, parking, floor,
    totalFloors, buildingAge, nearMetro, gym, pool, security,
    lift, balcony,
  } = inputs;

  const cityBase = {
    Mumbai: 55000, Delhi: 38000, Bangalore: 32000, Hyderabad: 24000,
    Chennai: 22000, Pune: 20000, Kolkata: 16000, Ahmedabad: 14000,
    Jaipur: 12000, Lucknow: 10000,
  };
  const base = cityBase[city] || 18000;
  const areaFactor = Math.pow(area / 1000, 0.72) * base;
  const bhkFactor = bhk * 0.18 * areaFactor;
  const furnMap = { Unfurnished: 1.0, "Semi-Furnished": 1.22, Furnished: 1.48 };
  const furnFactor = furnMap[furnishing] || 1.0;
  const amenities =
    (gym ? 0.06 : 0) + (pool ? 0.09 : 0) + (security ? 0.04 : 0) +
    (lift ? 0.03 : 0) + (balcony ? 0.02 : 0) + (parking ? 0.03 : 0) +
    (nearMetro ? 0.07 : 0);
  const floorBonus = floor > 5 ? 0.05 : floor > 10 ? 0.09 : 0;
  const agePenalty = buildingAge > 15 ? -0.08 : buildingAge > 25 ? -0.15 : 0;
  const bathBonus = (bathrooms - 1) * 0.04;
  let rent =
    (areaFactor + bhkFactor) * furnFactor * (1 + amenities + floorBonus + agePenalty + bathBonus);
  // Add noise for realism
  const seed = (city.charCodeAt(0) + area + bhk * 7) % 100;
  rent = rent * (1 + (seed - 50) / 500);
  const predicted = Math.round(rent / 100) * 100;
  const low = Math.round((predicted * 0.88) / 100) * 100;
  const high = Math.round((predicted * 1.13) / 100) * 100;
  const confidence = Math.min(96, 72 + seed * 0.24);
  const perSqft = Math.round(predicted / area);
  const percentile = Math.min(95, Math.max(20, 40 + ((predicted - base) / base) * 60));
  const importance = {
    "Area (sqft)": 28, City: 22, Furnishing: 16, "BHK": 12, Amenities: 10,
    "Floor/Age": 7, Other: 5,
  };
  return { predicted, low, high, confidence, perSqft, percentile, importance };
}

// ─── Mock data ─────────────────────────────────────────────────────
const CITIES = [
  "Mumbai","Delhi","Bangalore","Hyderabad","Chennai","Pune","Kolkata","Ahmedabad","Jaipur","Lucknow"
];
const HISTORY_MOCK = [
  { id: 1, city: "Bangalore", area: 1200, bhk: 2, furnishing: "Furnished", rent: 32000, date: "2025-04-10", confidence: 91 },
  { id: 2, city: "Mumbai", area: 900, bhk: 1, furnishing: "Semi-Furnished", rent: 48000, date: "2025-04-08", confidence: 88 },
  { id: 3, city: "Delhi", area: 1500, bhk: 3, furnishing: "Unfurnished", rent: 42000, date: "2025-03-30", confidence: 85 },
];
const TREND_DATA = {
  Mumbai: [52000,54000,53000,56000,55000,58000,57000,60000,59000,62000,61000,63000],
  Delhi: [36000,37000,36500,38000,38500,39000,38000,40000,41000,40500,42000,43000],
  Bangalore: [28000,29000,30000,31000,30500,32000,33000,32500,34000,34500,35000,36000],
  Hyderabad: [22000,23000,22500,24000,24500,25000,25500,26000,26500,27000,27500,28000],
  Chennai: [20000,20500,21000,21500,22000,22500,23000,23500,24000,24500,25000,25500],
};
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

// ─── Claude API helper ─────────────────────────────────────────────
async function askClaude(messages, system) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system,
      messages,
    }),
  });
  const data = await res.json();
  return data.content?.map((b) => b.text || "").join("") || "Sorry, I couldn't respond.";
}

// ─── Components ────────────────────────────────────────────────────

function Toast({ toasts, remove }) {
  return (
    <div style={{ position:"fixed", bottom:24, right:24, zIndex:9999, display:"flex", flexDirection:"column", gap:8 }}>
      {toasts.map((t) => (
        <div key={t.id} onClick={() => remove(t.id)} style={{
          background: t.type === "success" ? "#0d9f6e" : t.type === "error" ? "#e53e3e" : "#2d6aff",
          color:"#fff", padding:"10px 18px", borderRadius:10, fontSize:14, fontWeight:500,
          cursor:"pointer", boxShadow:"0 4px 20px rgba(0,0,0,0.3)",
          animation:"slideIn 0.3s ease",
          minWidth:240,
        }}>
          {t.msg}
        </div>
      ))}
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ display:"inline-block", width:20, height:20, border:"2px solid rgba(255,255,255,0.3)",
      borderTop:"2px solid #fff", borderRadius:"50%", animation:"spin 0.7s linear infinite" }} />
  );
}

function GlowCard({ children, style = {}, accent = "#6c63ff" }) {
  return (
    <div style={{
      background:"rgba(15,17,30,0.85)", border:`1px solid rgba(108,99,255,0.25)`,
      borderRadius:16, padding:24,
      boxShadow:`0 0 0 1px rgba(108,99,255,0.1), 0 8px 40px rgba(0,0,0,0.4)`,
      backdropFilter:"blur(10px)", ...style,
    }}>
      {children}
    </div>
  );
}

function Badge({ label, color = "#6c63ff" }) {
  return (
    <span style={{ background: color + "22", color, border: `1px solid ${color}44`,
      borderRadius:20, padding:"2px 10px", fontSize:11, fontWeight:600, letterSpacing:.5 }}>
      {label}
    </span>
  );
}

function Gauge({ value, max = 100, label, color = "#6c63ff" }) {
  const pct = value / max;
  const r = 44, cx = 54, cy = 54;
  const circ = 2 * Math.PI * r;
  const dash = pct * circ * 0.75;
  const gap = circ - dash;
  return (
    <div style={{ textAlign:"center" }}>
      <svg width={108} height={108} viewBox="0 0 108 108">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={9}
          strokeDasharray={`${circ * 0.75} ${circ * 0.25}`} strokeDashoffset={circ * 0.125}
          strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={9}
          strokeDasharray={`${dash} ${gap + circ * 0.25}`} strokeDashoffset={circ * 0.125}
          strokeLinecap="round" style={{ transition:"stroke-dasharray 1s ease" }} />
        <text x={cx} y={cy - 4} textAnchor="middle" fill="#fff" fontSize={18} fontWeight={700}>{Math.round(value)}</text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize={10}>{label}</text>
      </svg>
    </div>
  );
}

function BarChart({ data, color = "#6c63ff" }) {
  const max = Math.max(...Object.values(data));
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
      {Object.entries(data).map(([k, v]) => (
        <div key={k}>
          <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
            <span style={{ fontSize:12, color:"rgba(255,255,255,0.65)" }}>{k}</span>
            <span style={{ fontSize:12, color, fontWeight:600 }}>{v}%</span>
          </div>
          <div style={{ height:6, background:"rgba(255,255,255,0.07)", borderRadius:4, overflow:"hidden" }}>
            <div style={{ height:"100%", width:`${(v / max) * 100}%`, background:`linear-gradient(90deg,${color},${color}99)`,
              borderRadius:4, transition:"width 1s ease" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function LineChart({ cityData, city }) {
  const data = cityData[city] || Object.values(cityData)[0];
  const max = Math.max(...data) * 1.05;
  const min = Math.min(...data) * 0.95;
  const W = 460, H = 140;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * (W - 40) + 20;
    const y = H - ((v - min) / (max - min)) * (H - 30) - 15;
    return `${x},${y}`;
  });
  const path = "M " + pts.join(" L ");
  const area = `M ${pts[0]} L ${pts.join(" L ")} L ${(W - 20)},${H} L 20,${H} Z`;
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6c63ff" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#6c63ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#lineGrad)" />
      <path d={path} fill="none" stroke="#6c63ff" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
      {data.map((v, i) => {
        const x = (i / (data.length - 1)) * (W - 40) + 20;
        const y = H - ((v - min) / (max - min)) * (H - 30) - 15;
        return <circle key={i} cx={x} cy={y} r={3} fill="#6c63ff" />;
      })}
      {data.map((v, i) => {
        const x = (i / (data.length - 1)) * (W - 40) + 20;
        return <text key={i} x={x} y={H - 2} textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize={9}>{MONTHS[i]}</text>;
      })}
    </svg>
  );
}

// ─── Pages ─────────────────────────────────────────────────────────

function PredictorPage({ addToast, addHistory }) {
  const [form, setForm] = useState({
    city:"Bangalore", area:1000, bhk:2, bathrooms:2, furnishing:"Semi-Furnished",
    parking:true, floor:3, totalFloors:10, buildingAge:5, nearMetro:false,
    gym:false, pool:false, security:true, lift:true, balcony:true,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [expLoading, setExpLoading] = useState(false);

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (k) => () => setForm((f) => ({ ...f, [k]: !f[k] }));

  const handlePredict = async () => {
    setLoading(true); setResult(null); setExplanation("");
    await sleep(900);
    const r = predictRent(form);
    setResult(r);
    setLoading(false);
    addToast("Prediction complete!", "success");
    addHistory({ ...form, ...r, date: new Date().toISOString().split("T")[0], id: Date.now() });
    // AI explanation
    setExpLoading(true);
    try {
      const exp = await askClaude(
        [{ role:"user", content:`Explain in 3 sentences why a ${form.bhk}BHK ${form.furnishing} apartment of ${form.area} sqft in ${form.city} on floor ${form.floor}, ${form.buildingAge} years old, ${form.nearMetro?"near metro":"far from metro"}, with amenities: gym:${form.gym}, pool:${form.pool}, security:${form.security} would rent for approximately ₹${r.predicted.toLocaleString("en-IN")} per month. Be specific and insightful.` }],
        "You are RentIQ, an AI real estate analyst for Indian cities. Give concise, data-driven explanations."
      );
      setExplanation(exp);
    } catch {
      setExplanation("AI explanation unavailable — check your API key.");
    }
    setExpLoading(false);
  };

  const InputRow = ({ label, children }) => (
    <div style={{ marginBottom:16 }}>
      <label style={{ display:"block", fontSize:12, color:"rgba(255,255,255,0.5)", marginBottom:6, textTransform:"uppercase", letterSpacing:.8 }}>{label}</label>
      {children}
    </div>
  );
  const selectStyle = { width:"100%", background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.12)",
    color:"#fff", borderRadius:8, padding:"9px 12px", fontSize:14, outline:"none" };
  const inputStyle = { ...selectStyle };
  const ToggleBtn = ({ label, active, onClick }) => (
    <button onClick={onClick} style={{
      padding:"6px 14px", borderRadius:8, border:`1px solid ${active ? "#6c63ff" : "rgba(255,255,255,0.1)"}`,
      background: active ? "rgba(108,99,255,0.2)" : "transparent",
      color: active ? "#a8a3ff" : "rgba(255,255,255,0.45)", fontSize:13, cursor:"pointer",
    }}>{label}</button>
  );

  return (
    <div style={{ maxWidth:1100, margin:"0 auto", padding:"32px 24px" }}>
      <div style={{ marginBottom:28 }}>
        <h1 style={{ fontSize:28, fontWeight:700, color:"#fff", marginBottom:6 }}>Rent Predictor</h1>
        <p style={{ color:"rgba(255,255,255,0.45)", fontSize:15 }}>AI-powered rental estimation with market intelligence</p>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:24 }}>
        {/* Form */}
        <GlowCard>
          <h3 style={{ color:"#fff", marginBottom:20, fontSize:16, fontWeight:600 }}>Property Details</h3>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"0 16px" }}>
            <InputRow label="City">
              <select style={selectStyle} value={form.city} onChange={(e) => set("city")(e.target.value)}>
                {CITIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </InputRow>
            <InputRow label="Area (sqft)">
              <input type="number" style={inputStyle} value={form.area} onChange={(e) => set("area")(+e.target.value)} min={100} max={10000} />
            </InputRow>
            <InputRow label="BHK">
              <select style={selectStyle} value={form.bhk} onChange={(e) => set("bhk")(+e.target.value)}>
                {[1,2,3,4,5].map((n) => <option key={n}>{n}</option>)}
              </select>
            </InputRow>
            <InputRow label="Bathrooms">
              <select style={selectStyle} value={form.bathrooms} onChange={(e) => set("bathrooms")(+e.target.value)}>
                {[1,2,3,4].map((n) => <option key={n}>{n}</option>)}
              </select>
            </InputRow>
            <InputRow label="Furnishing">
              <select style={selectStyle} value={form.furnishing} onChange={(e) => set("furnishing")(e.target.value)}>
                {["Unfurnished","Semi-Furnished","Furnished"].map((f) => <option key={f}>{f}</option>)}
              </select>
            </InputRow>
            <InputRow label="Floor">
              <input type="number" style={inputStyle} value={form.floor} onChange={(e) => set("floor")(+e.target.value)} min={0} max={50} />
            </InputRow>
            <InputRow label="Total Floors">
              <input type="number" style={inputStyle} value={form.totalFloors} onChange={(e) => set("totalFloors")(+e.target.value)} min={1} max={80} />
            </InputRow>
            <InputRow label="Building Age (yrs)">
              <input type="number" style={inputStyle} value={form.buildingAge} onChange={(e) => set("buildingAge")(+e.target.value)} min={0} max={60} />
            </InputRow>
          </div>
          <InputRow label="Amenities">
            <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
              {[["gym","Gym"],["pool","Pool"],["security","Security"],["lift","Lift"],["balcony","Balcony"],["parking","Parking"],["nearMetro","Near Metro"]].map(([k,l]) => (
                <ToggleBtn key={k} label={l} active={form[k]} onClick={toggle(k)} />
              ))}
            </div>
          </InputRow>
          <button onClick={handlePredict} disabled={loading} style={{
            width:"100%", padding:"14px", background: loading ? "rgba(108,99,255,0.4)" : "linear-gradient(135deg,#6c63ff,#4834d4)",
            border:"none", borderRadius:10, color:"#fff", fontSize:15, fontWeight:700,
            cursor: loading ? "not-allowed" : "pointer", marginTop:8, display:"flex", alignItems:"center", justifyContent:"center", gap:10,
          }}>
            {loading ? <><Spinner /> Predicting...</> : "⚡ Predict Rent"}
          </button>
        </GlowCard>

        {/* Results */}
        <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
          {result ? (
            <>
              <GlowCard style={{ background:"linear-gradient(135deg,rgba(108,99,255,0.15),rgba(72,52,212,0.1))" }}>
                <div style={{ textAlign:"center", marginBottom:16 }}>
                  <div style={{ fontSize:12, color:"rgba(255,255,255,0.5)", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Predicted Monthly Rent</div>
                  <div style={{ fontSize:42, fontWeight:800, color:"#fff", letterSpacing:-1 }}>{fmt(result.predicted)}</div>
                  <div style={{ color:"rgba(255,255,255,0.45)", fontSize:13, marginTop:4 }}>Range: {fmt(result.low)} – {fmt(result.high)}</div>
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12 }}>
                  {[
                    ["Confidence", rnd(result.confidence, 1) + "%", "#0d9f6e"],
                    ["Per sqft", fmt(result.perSqft), "#f59e0b"],
                    ["Percentile", rnd(result.percentile) + "%", "#e879f9"],
                  ].map(([l, v, c]) => (
                    <div key={l} style={{ background:"rgba(255,255,255,0.05)", borderRadius:10, padding:"12px 10px", textAlign:"center" }}>
                      <div style={{ fontSize:18, fontWeight:700, color:c }}>{v}</div>
                      <div style={{ fontSize:11, color:"rgba(255,255,255,0.45)", marginTop:3 }}>{l}</div>
                    </div>
                  ))}
                </div>
              </GlowCard>
              <GlowCard>
                <h4 style={{ color:"#fff", marginBottom:16, fontSize:14 }}>Feature Importance</h4>
                <BarChart data={result.importance} />
              </GlowCard>
              {(explanation || expLoading) && (
                <GlowCard style={{ borderColor:"rgba(232,121,249,0.25)" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12 }}>
                    <span style={{ fontSize:18 }}>🤖</span>
                    <h4 style={{ color:"#e879f9", fontSize:14, margin:0 }}>AI Analysis</h4>
                    {expLoading && <Spinner />}
                  </div>
                  {explanation && <p style={{ color:"rgba(255,255,255,0.75)", fontSize:14, lineHeight:1.7, margin:0 }}>{explanation}</p>}
                </GlowCard>
              )}
            </>
          ) : (
            <GlowCard style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", minHeight:320, textAlign:"center" }}>
              <div style={{ fontSize:64, marginBottom:16, opacity:0.3 }}>🏡</div>
              <p style={{ color:"rgba(255,255,255,0.3)", fontSize:15 }}>Fill in the property details and click Predict Rent to get your AI-powered estimate</p>
            </GlowCard>
          )}
        </div>
      </div>
    </div>
  );
}

function DashboardPage({ history }) {
  const [activeCity, setActiveCity] = useState("Bangalore");
  const totalPredictions = history.length + HISTORY_MOCK.length;
  const avgRent = history.length > 0
    ? Math.round(history.reduce((s, h) => s + h.predicted, 0) / history.length)
    : 28500;

  return (
    <div style={{ maxWidth:1100, margin:"0 auto", padding:"32px 24px" }}>
      <div style={{ marginBottom:28 }}>
        <h1 style={{ fontSize:28, fontWeight:700, color:"#fff", marginBottom:6 }}>Dashboard</h1>
        <p style={{ color:"rgba(255,255,255,0.45)", fontSize:15 }}>Market insights & prediction analytics</p>
      </div>

      {/* Stats */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:16, marginBottom:24 }}>
        {[
          ["Predictions", totalPredictions, "#6c63ff", "📊"],
          ["Avg Rent", fmt(avgRent), "#0d9f6e", "💰"],
          ["Cities Tracked", 10, "#f59e0b", "🏙️"],
          ["AI Accuracy", "91.4%", "#e879f9", "🎯"],
        ].map(([l, v, c, icon]) => (
          <GlowCard key={l} style={{ padding:20, textAlign:"center" }}>
            <div style={{ fontSize:28, marginBottom:8 }}>{icon}</div>
            <div style={{ fontSize:24, fontWeight:800, color:c }}>{v}</div>
            <div style={{ fontSize:12, color:"rgba(255,255,255,0.4)", marginTop:4 }}>{l}</div>
          </GlowCard>
        ))}
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"3fr 2fr", gap:24, marginBottom:24 }}>
        {/* Trend chart */}
        <GlowCard>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
            <h3 style={{ color:"#fff", fontSize:15, fontWeight:600 }}>Rent Trend (12 months)</h3>
            <div style={{ display:"flex", gap:6 }}>
              {["Bangalore","Mumbai","Delhi","Hyderabad"].map((c) => (
                <button key={c} onClick={() => setActiveCity(c)} style={{
                  padding:"4px 10px", borderRadius:6, fontSize:12, cursor:"pointer",
                  background: activeCity === c ? "rgba(108,99,255,0.3)" : "transparent",
                  border: `1px solid ${activeCity === c ? "#6c63ff" : "rgba(255,255,255,0.1)"}`,
                  color: activeCity === c ? "#a8a3ff" : "rgba(255,255,255,0.4)",
                }}>{c}</button>
              ))}
            </div>
          </div>
          <LineChart cityData={TREND_DATA} city={activeCity} />
        </GlowCard>

        {/* City comparison */}
        <GlowCard>
          <h3 style={{ color:"#fff", fontSize:15, fontWeight:600, marginBottom:16 }}>City Avg Rent (2BHK)</h3>
          <BarChart data={{
            Mumbai: 100, Delhi: 72, Bangalore: 61, Hyderabad: 46, Chennai: 42,
          }} color="#0d9f6e" />
          <p style={{ fontSize:11, color:"rgba(255,255,255,0.3)", marginTop:12 }}>Index: Mumbai = 100</p>
        </GlowCard>
      </div>

      {/* Prediction history */}
      <GlowCard>
        <h3 style={{ color:"#fff", fontSize:15, fontWeight:600, marginBottom:16 }}>Recent Predictions</h3>
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:14 }}>
            <thead>
              <tr>
                {["City","Area","BHK","Furnishing","Predicted Rent","Confidence","Date"].map((h) => (
                  <th key={h} style={{ textAlign:"left", padding:"8px 12px", color:"rgba(255,255,255,0.4)", fontSize:12, textTransform:"uppercase", borderBottom:"1px solid rgba(255,255,255,0.08)" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...history.slice(-5).reverse(), ...HISTORY_MOCK].map((row, i) => (
                <tr key={i} style={{ borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
                  <td style={{ padding:"10px 12px", color:"#fff" }}>{row.city}</td>
                  <td style={{ padding:"10px 12px", color:"rgba(255,255,255,0.7)" }}>{row.area} sqft</td>
                  <td style={{ padding:"10px 12px", color:"rgba(255,255,255,0.7)" }}>{row.bhk}BHK</td>
                  <td style={{ padding:"10px 12px" }}><Badge label={row.furnishing || "Semi-Furnished"} color="#6c63ff" /></td>
                  <td style={{ padding:"10px 12px", color:"#0d9f6e", fontWeight:700 }}>{fmt(row.predicted || row.rent)}</td>
                  <td style={{ padding:"10px 12px", color:"#f59e0b" }}>{rnd(row.confidence || 88)}%</td>
                  <td style={{ padding:"10px 12px", color:"rgba(255,255,255,0.4)" }}>{row.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlowCard>
    </div>
  );
}

function ModelMetricsPage() {
  const models = [
    { name:"Random Forest", r2:0.934, mae:2840, rmse:3960, accuracy:93.4, color:"#6c63ff", badge:"Best" },
    { name:"XGBoost", r2:0.921, mae:3120, rmse:4280, accuracy:92.1, color:"#0d9f6e", badge:"Fast" },
    { name:"Neural Network", r2:0.908, mae:3450, rmse:4710, accuracy:90.8, color:"#e879f9", badge:"Deep" },
    { name:"Linear Regression", r2:0.823, mae:5200, rmse:7100, accuracy:82.3, color:"#f59e0b", badge:"Baseline" },
  ];
  return (
    <div style={{ maxWidth:1100, margin:"0 auto", padding:"32px 24px" }}>
      <div style={{ marginBottom:28 }}>
        <h1 style={{ fontSize:28, fontWeight:700, color:"#fff", marginBottom:6 }}>ML Model Metrics</h1>
        <p style={{ color:"rgba(255,255,255,0.45)", fontSize:15 }}>Comparative performance of trained regression models</p>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(2,1fr)", gap:20, marginBottom:28 }}>
        {models.map((m) => (
          <GlowCard key={m.name} style={{ borderColor: m.badge === "Best" ? "rgba(108,99,255,0.5)" : undefined }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20 }}>
              <div>
                <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                  <h3 style={{ color:"#fff", fontSize:16, fontWeight:700, margin:0 }}>{m.name}</h3>
                  <Badge label={m.badge} color={m.color} />
                </div>
              </div>
              <Gauge value={m.accuracy} label="Accuracy" color={m.color} />
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:10 }}>
              {[["R² Score", rnd(m.r2,3)], ["MAE (₹)", m.mae.toLocaleString("en-IN")], ["RMSE (₹)", m.rmse.toLocaleString("en-IN")]].map(([k,v]) => (
                <div key={k} style={{ background:"rgba(255,255,255,0.04)", borderRadius:8, padding:"10px", textAlign:"center" }}>
                  <div style={{ fontSize:16, fontWeight:700, color:m.color }}>{v}</div>
                  <div style={{ fontSize:11, color:"rgba(255,255,255,0.35)", marginTop:3 }}>{k}</div>
                </div>
              ))}
            </div>
          </GlowCard>
        ))}
      </div>

      <GlowCard>
        <h3 style={{ color:"#fff", fontSize:15, fontWeight:600, marginBottom:20 }}>Model Comparison — R² Score</h3>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {models.map((m) => (
            <div key={m.name} style={{ display:"flex", alignItems:"center", gap:16 }}>
              <span style={{ width:140, fontSize:13, color:"rgba(255,255,255,0.7)" }}>{m.name}</span>
              <div style={{ flex:1, height:10, background:"rgba(255,255,255,0.06)", borderRadius:5, overflow:"hidden" }}>
                <div style={{ height:"100%", width:`${m.r2*100}%`, background:`linear-gradient(90deg,${m.color},${m.color}88)`, borderRadius:5, transition:"width 1.2s ease" }} />
              </div>
              <span style={{ width:50, fontSize:13, color:m.color, fontWeight:700 }}>{rnd(m.r2,3)}</span>
            </div>
          ))}
        </div>
      </GlowCard>
    </div>
  );
}

function ChatbotPage() {
  const [messages, setMessages] = useState([
    { role:"assistant", content:"Hi! I'm **RentIQ AI**, your real estate intelligence assistant. Ask me anything about rent, market trends, property advice, or tenant/landlord guidance! 🏡" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef();
  const SYSTEM = `You are RentIQ AI, a smart, friendly real estate assistant specializing in Indian rental markets. You help with: rent estimation, market trends, investment advice, tenant rights, landlord guidance, locality recommendations, budget planning, lease agreement tips. Be concise, helpful, and use ₹ for prices. Always provide actionable insights. Keep responses under 150 words.`;

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role:"user", content:userMsg }]);
    setLoading(true);
    try {
      const history = messages.concat([{ role:"user", content:userMsg }])
        .filter((m) => m.role !== "assistant" || messages.indexOf(m) > 0)
        .map((m) => ({ role: m.role === "assistant" ? "assistant" : "user", content: m.content }));
      const reply = await askClaude(history.slice(-10), SYSTEM);
      setMessages((m) => [...m, { role:"assistant", content:reply }]);
    } catch {
      setMessages((m) => [...m, { role:"assistant", content:"Connection error. Please check your API configuration." }]);
    }
    setLoading(false);
  };

  const QUICK = ["Best cities for rent under ₹20k?","Is Bangalore rent overpriced?","Tips for first-time tenants","2BHK vs 3BHK investment?"];

  return (
    <div style={{ maxWidth:780, margin:"0 auto", padding:"32px 24px", height:"calc(100vh - 80px)", display:"flex", flexDirection:"column" }}>
      <div style={{ marginBottom:20 }}>
        <h1 style={{ fontSize:28, fontWeight:700, color:"#fff", marginBottom:4 }}>AI Assistant</h1>
        <p style={{ color:"rgba(255,255,255,0.45)", fontSize:15 }}>Powered by Claude — Real estate intelligence at your fingertips</p>
      </div>

      <GlowCard style={{ flex:1, display:"flex", flexDirection:"column", padding:0, overflow:"hidden" }}>
        {/* Messages */}
        <div style={{ flex:1, overflowY:"auto", padding:24, display:"flex", flexDirection:"column", gap:16, scrollbarWidth:"thin", scrollbarColor:"rgba(108,99,255,0.3) transparent" }}>
          {messages.map((m, i) => (
            <div key={i} style={{ display:"flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", gap:10 }}>
              {m.role === "assistant" && (
                <div style={{ width:32, height:32, borderRadius:"50%", background:"linear-gradient(135deg,#6c63ff,#e879f9)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, flexShrink:0, marginTop:4 }}>🤖</div>
              )}
              <div style={{
                maxWidth:"75%", padding:"12px 16px", borderRadius: m.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                background: m.role === "user" ? "linear-gradient(135deg,#6c63ff,#4834d4)" : "rgba(255,255,255,0.06)",
                border: m.role === "user" ? "none" : "1px solid rgba(255,255,255,0.08)",
                color:"rgba(255,255,255,0.9)", fontSize:14, lineHeight:1.65,
                whiteSpace:"pre-wrap",
              }}>{m.content.replace(/\*\*(.*?)\*\*/g, "$1")}</div>
            </div>
          ))}
          {loading && (
            <div style={{ display:"flex", gap:10, alignItems:"flex-start" }}>
              <div style={{ width:32, height:32, borderRadius:"50%", background:"linear-gradient(135deg,#6c63ff,#e879f9)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14 }}>🤖</div>
              <div style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:"18px 18px 18px 4px", padding:"14px 18px", display:"flex", gap:5, alignItems:"center" }}>
                {[0,1,2].map((d) => (
                  <div key={d} style={{ width:7, height:7, borderRadius:"50%", background:"#6c63ff", animation:`bounce 1s ease ${d*0.2}s infinite` }} />
                ))}
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Quick actions */}
        <div style={{ padding:"12px 24px 0", borderTop:"1px solid rgba(255,255,255,0.06)", display:"flex", flexWrap:"wrap", gap:6 }}>
          {QUICK.map((q) => (
            <button key={q} onClick={() => { setInput(q); }} style={{
              padding:"5px 12px", borderRadius:20, fontSize:12, cursor:"pointer",
              background:"rgba(108,99,255,0.1)", border:"1px solid rgba(108,99,255,0.3)",
              color:"#a8a3ff",
            }}>{q}</button>
          ))}
        </div>

        {/* Input */}
        <div style={{ padding:"16px 24px", display:"flex", gap:10 }}>
          <input
            value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask about rent, market trends, property advice..."
            style={{ flex:1, background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)",
              borderRadius:12, padding:"12px 16px", color:"#fff", fontSize:14, outline:"none" }}
          />
          <button onClick={send} disabled={loading || !input.trim()} style={{
            padding:"12px 20px", background:"linear-gradient(135deg,#6c63ff,#4834d4)",
            border:"none", borderRadius:12, color:"#fff", fontWeight:700, cursor: loading ? "not-allowed" : "pointer", fontSize:14,
          }}>Send</button>
        </div>
      </GlowCard>
    </div>
  );
}

function MarketPage() {
  const [city, setCity] = useState("Bangalore");
  const [aiInsight, setAiInsight] = useState("");
  const [insightLoading, setInsightLoading] = useState(false);

  const getInsight = async () => {
    setInsightLoading(true); setAiInsight("");
    try {
      const resp = await askClaude(
        [{ role:"user", content:`Give a 4-bullet market analysis for the ${city} rental market in 2025. Include: demand drivers, price outlook, best localities, investment potential. Be specific and data-driven.` }],
        "You are a senior real estate market analyst. Provide insightful, actionable analysis."
      );
      setAiInsight(resp);
    } catch { setAiInsight("AI insight unavailable."); }
    setInsightLoading(false);
  };

  const cityStats = {
    Mumbai: { avgRent:55000, yoy:"+8.2%", demand:"Very High", best:["Bandra","Powai","Andheri"], forecast:"+6%" },
    Delhi: { avgRent:38000, yoy:"+5.1%", demand:"High", best:["Gurugram","Noida","Dwarka"], forecast:"+5%" },
    Bangalore: { avgRent:32000, yoy:"+11.4%", demand:"Very High", best:["Whitefield","Koramangala","HSR Layout"], forecast:"+9%" },
    Hyderabad: { avgRent:24000, yoy:"+9.2%", demand:"High", best:["Gachibowli","Kondapur","Banjara Hills"], forecast:"+8%" },
    Chennai: { avgRent:22000, yoy:"+6.8%", demand:"Moderate", best:["Anna Nagar","OMR","Velachery"], forecast:"+5%" },
    Pune: { avgRent:20000, yoy:"+7.5%", demand:"High", best:["Kothrud","Baner","Hinjawadi"], forecast:"+7%" },
    Kolkata: { avgRent:16000, yoy:"+3.2%", demand:"Moderate", best:["Salt Lake","New Town","Ballygunge"], forecast:"+4%" },
    Ahmedabad: { avgRent:14000, yoy:"+4.8%", demand:"Moderate", best:["Prahlad Nagar","SG Road","Satellite"], forecast:"+5%" },
    Jaipur: { avgRent:12000, yoy:"+5.5%", demand:"Moderate", best:["Vaishali Nagar","Malviya Nagar","C-Scheme"], forecast:"+5%" },
    Lucknow: { avgRent:10000, yoy:"+4.1%", demand:"Low-Moderate", best:["Gomti Nagar","Hazratganj","Indira Nagar"], forecast:"+4%" },
  };
  const stats = cityStats[city] || cityStats.Bangalore;

  return (
    <div style={{ maxWidth:1100, margin:"0 auto", padding:"32px 24px" }}>
      <div style={{ marginBottom:28 }}>
        <h1 style={{ fontSize:28, fontWeight:700, color:"#fff", marginBottom:6 }}>Market Intelligence</h1>
        <p style={{ color:"rgba(255,255,255,0.45)", fontSize:15 }}>Live rental market data & AI-powered city analysis</p>
      </div>

      <div style={{ display:"flex", gap:8, marginBottom:24, flexWrap:"wrap" }}>
        {CITIES.map((c) => (
          <button key={c} onClick={() => setCity(c)} style={{
            padding:"8px 16px", borderRadius:8, fontSize:13, cursor:"pointer",
            background: city === c ? "rgba(108,99,255,0.25)" : "rgba(255,255,255,0.04)",
            border: `1px solid ${city === c ? "#6c63ff" : "rgba(255,255,255,0.1)"}`,
            color: city === c ? "#a8a3ff" : "rgba(255,255,255,0.5)",
          }}>{c}</button>
        ))}
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:16, marginBottom:24 }}>
        {[
          ["Avg Rent (2BHK)", fmt(stats.avgRent), "#6c63ff"],
          ["YoY Growth", stats.yoy, "#0d9f6e"],
          ["Demand", stats.demand, "#f59e0b"],
          ["2026 Forecast", stats.forecast, "#e879f9"],
        ].map(([l, v, c]) => (
          <GlowCard key={l} style={{ textAlign:"center", padding:20 }}>
            <div style={{ fontSize:22, fontWeight:800, color:c }}>{v}</div>
            <div style={{ fontSize:12, color:"rgba(255,255,255,0.4)", marginTop:6 }}>{l}</div>
          </GlowCard>
        ))}
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:24, marginBottom:24 }}>
        <GlowCard>
          <h3 style={{ color:"#fff", fontSize:15, marginBottom:16 }}>Top Localities — {city}</h3>
          {stats.best.map((loc, i) => (
            <div key={loc} style={{ display:"flex", alignItems:"center", gap:12, padding:"10px 0",
              borderBottom: i < stats.best.length - 1 ? "1px solid rgba(255,255,255,0.06)" : "none" }}>
              <div style={{ width:28, height:28, borderRadius:"50%", background:"rgba(108,99,255,0.2)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:12, color:"#6c63ff", fontWeight:700 }}>{i+1}</div>
              <div style={{ flex:1 }}>
                <div style={{ color:"#fff", fontSize:14, fontWeight:600 }}>{loc}</div>
                <div style={{ color:"rgba(255,255,255,0.4)", fontSize:12 }}>High demand · {["Premium","Mid-range","Luxury"][i % 3]}</div>
              </div>
              <Badge label={["🔥 Hot","📈 Rising","⭐ Top"][i % 3]} color={["#e53e3e","#f59e0b","#0d9f6e"][i % 3]} />
            </div>
          ))}
        </GlowCard>

        <GlowCard>
          <h3 style={{ color:"#fff", fontSize:15, marginBottom:16 }}>12-Month Rent Trend</h3>
          <LineChart cityData={TREND_DATA} city={city.includes("Hyderabad") ? "Hyderabad" : city.includes("Delhi") ? "Delhi" : city.includes("Mumbai") ? "Mumbai" : city === "Chennai" ? "Chennai" : "Bangalore"} />
        </GlowCard>
      </div>

      <GlowCard>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <h3 style={{ color:"#fff", fontSize:15 }}>AI Market Analysis — {city}</h3>
          <button onClick={getInsight} disabled={insightLoading} style={{
            padding:"8px 18px", background:"linear-gradient(135deg,#e879f9,#6c63ff)",
            border:"none", borderRadius:8, color:"#fff", fontSize:13, fontWeight:600, cursor: insightLoading ? "not-allowed" : "pointer",
            display:"flex", alignItems:"center", gap:8,
          }}>
            {insightLoading ? <><Spinner /> Analyzing...</> : "🤖 Generate AI Insight"}
          </button>
        </div>
        {aiInsight ? (
          <p style={{ color:"rgba(255,255,255,0.75)", fontSize:14, lineHeight:1.75, whiteSpace:"pre-wrap" }}>{aiInsight}</p>
        ) : (
          <p style={{ color:"rgba(255,255,255,0.3)", fontSize:14 }}>Click "Generate AI Insight" to get a detailed market analysis powered by Claude AI.</p>
        )}
      </GlowCard>
    </div>
  );
}

// ─── Main App ──────────────────────────────────────────────────────
export default function RentIQ() {
  const [page, setPage] = useState("predict");
  const [toasts, setToasts] = useState([]);
  const [history, setHistory] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const addToast = useCallback((msg, type = "info") => {
    const id = Date.now();
    setToasts((t) => [...t, { id, msg, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);
  const removeToast = (id) => setToasts((t) => t.filter((x) => x.id !== id));
  const addHistory = (entry) => setHistory((h) => [...h, entry]);

  const NAV = [
    { id:"predict", icon:"⚡", label:"Predict" },
    { id:"dashboard", icon:"📊", label:"Dashboard" },
    { id:"market", icon:"🏙️", label:"Market" },
    { id:"models", icon:"🧠", label:"ML Models" },
    { id:"chat", icon:"🤖", label:"AI Chat" },
  ];

  const PAGES = { predict: PredictorPage, dashboard: DashboardPage, market: MarketPage, models: ModelMetricsPage, chat: ChatbotPage };
  const ActivePage = PAGES[page] || PredictorPage;

  return (
    <div style={{ minHeight:"100vh", background:"#080a14", fontFamily:"'DM Sans',system-ui,sans-serif", color:"#fff", display:"flex" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:5px; height:5px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:rgba(108,99,255,0.3); border-radius:3px; }
        select option { background:#1a1c2e; color:#fff; }
        @keyframes spin { to { transform:rotate(360deg); } }
        @keyframes bounce { 0%,80%,100% { transform:scale(0); opacity:.5; } 40% { transform:scale(1); opacity:1; } }
        @keyframes slideIn { from { transform:translateX(40px); opacity:0; } to { transform:translateX(0); opacity:1; } }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }
        input[type=number]::-webkit-inner-spin-button { opacity:.4; }
        button { font-family:inherit; }
        select { font-family:inherit; cursor:pointer; }
        input { font-family:inherit; }
      `}</style>

      {/* Background orbs */}
      <div style={{ position:"fixed", inset:0, pointerEvents:"none", overflow:"hidden", zIndex:0 }}>
        <div style={{ position:"absolute", width:600, height:600, borderRadius:"50%", background:"radial-gradient(circle,rgba(108,99,255,0.07) 0%,transparent 70%)", top:-200, left:-100 }} />
        <div style={{ position:"absolute", width:500, height:500, borderRadius:"50%", background:"radial-gradient(circle,rgba(232,121,249,0.05) 0%,transparent 70%)", bottom:-100, right:200 }} />
        <div style={{ position:"absolute", width:400, height:400, borderRadius:"50%", background:"radial-gradient(circle,rgba(13,159,110,0.04) 0%,transparent 70%)", top:"40%", left:"50%" }} />
      </div>

      {/* Sidebar */}
      <div style={{
        width: sidebarOpen ? 220 : 64, flexShrink:0, background:"rgba(255,255,255,0.02)",
        borderRight:"1px solid rgba(255,255,255,0.06)", display:"flex", flexDirection:"column",
        position:"sticky", top:0, height:"100vh", zIndex:10, transition:"width 0.25s ease",
      }}>
        {/* Logo */}
        <div style={{ padding: sidebarOpen ? "24px 20px 20px" : "24px 16px 20px", borderBottom:"1px solid rgba(255,255,255,0.06)", display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ width:34, height:34, borderRadius:10, background:"linear-gradient(135deg,#6c63ff,#e879f9)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, flexShrink:0 }}>🏡</div>
          {sidebarOpen && <span style={{ fontSize:20, fontWeight:800, color:"#fff", letterSpacing:-.5 }}>RentIQ</span>}
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:"16px 10px", display:"flex", flexDirection:"column", gap:4 }}>
          {NAV.map((n) => (
            <button key={n.id} onClick={() => setPage(n.id)} style={{
              display:"flex", alignItems:"center", gap:12, padding: sidebarOpen ? "11px 14px" : "11px", borderRadius:10,
              background: page === n.id ? "rgba(108,99,255,0.2)" : "transparent",
              border: `1px solid ${page === n.id ? "rgba(108,99,255,0.4)" : "transparent"}`,
              color: page === n.id ? "#a8a3ff" : "rgba(255,255,255,0.45)",
              cursor:"pointer", fontSize:20, fontWeight:600, transition:"all 0.15s",
              justifyContent: sidebarOpen ? "flex-start" : "center",
            }}>
              <span>{n.icon}</span>
              {sidebarOpen && <span style={{ fontSize:14 }}>{n.label}</span>}
              {sidebarOpen && page === n.id && <div style={{ marginLeft:"auto", width:5, height:5, borderRadius:"50%", background:"#6c63ff" }} />}
            </button>
          ))}
        </nav>

        {/* Toggle */}
        <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{
          margin:12, padding:"10px", borderRadius:10, background:"rgba(255,255,255,0.04)",
          border:"1px solid rgba(255,255,255,0.08)", color:"rgba(255,255,255,0.4)",
          cursor:"pointer", fontSize:14, display:"flex", alignItems:"center", justifyContent:"center",
        }}>{sidebarOpen ? "←" : "→"}</button>
      </div>

      {/* Main */}
      <main style={{ flex:1, overflowY:"auto", position:"relative", zIndex:1 }}>
        {/* Topbar */}
        <div style={{ position:"sticky", top:0, background:"rgba(8,10,20,0.9)", borderBottom:"1px solid rgba(255,255,255,0.06)", backdropFilter:"blur(12px)", padding:"14px 28px", display:"flex", justifyContent:"space-between", alignItems:"center", zIndex:5 }}>
          <div>
            <span style={{ fontSize:13, color:"rgba(255,255,255,0.35)" }}>RentIQ AI Platform</span>
            <span style={{ margin:"0 8px", color:"rgba(255,255,255,0.15)" }}>›</span>
            <span style={{ fontSize:13, color:"rgba(255,255,255,0.7)", fontWeight:500 }}>{NAV.find(n => n.id === page)?.label}</span>
          </div>
          <div style={{ display:"flex", gap:10, alignItems:"center" }}>
            <Badge label="Beta" color="#f59e0b" />
            <div style={{ width:32, height:32, borderRadius:"50%", background:"linear-gradient(135deg,#6c63ff,#e879f9)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, cursor:"pointer" }}>👤</div>
          </div>
        </div>

        <ActivePage addToast={addToast} addHistory={addHistory} history={history} />
      </main>

      <Toast toasts={toasts} remove={removeToast} />
    </div>
  );
}
