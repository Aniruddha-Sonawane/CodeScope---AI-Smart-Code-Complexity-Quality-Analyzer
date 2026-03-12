import { useState, useMemo, useRef } from "react";
import "./App.css";
import Editor from "@monaco-editor/react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid
} from "recharts";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import logoImg from "./assets/logo.png";
import githubLogo from "./assets/github.png";
import linkedinLogo from "./assets/linkedin.png";

const API_BASE =
  import.meta.env.VITE_API_URL ||
  "https://ai-based-code-complexity-and-risk.onrender.com";

const COLORS = {
  bg: "#020617",
  card: "#0f172a",
  border: "#1e293b",
  textMain: "#f8fafc",
  textMuted: "#94a3b8",
  primary: "#6366f1",
  accent: "#22d3ee",
  danger: "#ef4444",
  modalOverlay: "rgba(0, 0, 0, 0.9)"
};

// ─── Language config ────────────────────────────────────────────────────────
const LANGUAGES = [
  { value: "python",     label: "Python",     monacoId: "python" },
  { value: "javascript", label: "JavaScript", monacoId: "javascript" },
  { value: "java",       label: "Java",       monacoId: "java" },
  { value: "c",          label: "C",          monacoId: "c" },
  { value: "cpp",        label: "C++",        monacoId: "cpp" },
];

const DEFAULT_SNIPPETS: Record<string, string> = {
  python: `def example():\n    for i in range(10):\n        if i % 2 == 0:\n            print(i)`,
  javascript: `function example() {\n    for (let i = 0; i < 10; i++) {\n        if (i % 2 === 0) {\n            console.log(i);\n        }\n    }\n}`,
  java: `public class Example {\n    public static void main(String[] args) {\n        for (int i = 0; i < 10; i++) {\n            if (i % 2 == 0) {\n                System.out.println(i);\n            }\n        }\n    }\n}`,
  c: `#include <stdio.h>\n\nint main() {\n    for (int i = 0; i < 10; i++) {\n        if (i % 2 == 0) {\n            printf("%d\\n", i);\n        }\n    }\n    return 0;\n}`,
  cpp: `#include <iostream>\nusing namespace std;\n\nint main() {\n    for (int i = 0; i < 10; i++) {\n        if (i % 2 == 0) {\n            cout << i << endl;\n        }\n    }\n    return 0;\n}`,
};
// ────────────────────────────────────────────────────────────────────────────

const modalStyle: React.CSSProperties = {
  position: "fixed",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  background: COLORS.card,
  border: `1px solid ${COLORS.border}`,
  borderRadius: "20px",
  padding: "24px",
  zIndex: 1001,
  width: "90%",
  maxWidth: "850px",
  height: "500px",
  display: "flex",
  flexDirection: "column",
  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8)",
  overflow: "hidden"
};

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  top: 0, left: 0, right: 0, bottom: 0,
  background: COLORS.modalOverlay,
  backdropFilter: "blur(8px)",
  zIndex: 1000
};

function badge(text: string) {
  let color = COLORS.textMuted;
  if (text.includes("Low") || text.includes("Excellent")) color = "#10b981";
  else if (text.includes("High") || text.includes("Poor")) color = COLORS.danger;

  return (
    <span style={{
      background: `${color}15`,
      color: color,
      padding: "4px 10px",
      borderRadius: "12px",
      fontSize: "0.7rem",
      fontWeight: "bold",
      border: `1px solid ${color}33`
    }}>{text}</span>
  );
}

function riskColor(riskText: string) {
  const risk = riskText.toLowerCase();
  if (risk.includes("high")) return COLORS.danger;
  if (risk.includes("medium")) return "#f59e0b";
  if (risk.includes("low")) return "#10b981";
  return COLORS.textMuted;
}

export default function App() {
  const editorRef = useRef<any>(null);

  // ── NEW: language state ──────────────────────────────────────────────────
  const [language, setLanguage] = useState<string>("python");
  // ────────────────────────────────────────────────────────────────────────

  const [code, setCode] = useState<string>(DEFAULT_SNIPPETS["python"]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [isEditorExpanded, setIsEditorExpanded] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isGraphZoomOpen, setIsGraphZoomOpen] = useState(false);
  const [isSearchVisible, setIsSearchVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredFunctions = useMemo(() => {
    if (!result?.functions) return [];
    return result.functions.filter((fn: any) =>
      fn.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [result, searchTerm]);

  // ── NEW: switch language & load default snippet ──────────────────────────
  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    setCode(DEFAULT_SNIPPETS[lang] || "");
    setResult(null);
  };
  // ────────────────────────────────────────────────────────────────────────

  const handleFunctionClick = (line: number) => {
    setIsGraphZoomOpen(false);
    if (editorRef.current && line) {
      editorRef.current.revealLineInCenter(line);
      editorRef.current.setPosition({ lineNumber: line, column: 1 });
      editorRef.current.focus();
    }
  };

  async function analyze() {
    setLoading(true);
    const startTime = Date.now();
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // ── CHANGED: send language alongside code ──────────────────────────
        body: JSON.stringify({ code, language })
        // ──────────────────────────────────────────────────────────────────
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error("Backend not connected");
    }
    const elapsed = Date.now() - startTime;
    const minDuration = 1000;
    if (elapsed < minDuration) {
      await new Promise((resolve) => setTimeout(resolve, minDuration - elapsed));
    }
    setLoading(false);
  }

  function downloadReport() {
    if (!result) return;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const cleanStr = (str: string) => str.replace(/[^\x00-\x7F]/g, "").trim();

    doc.setFillColor(15, 23, 42);
    doc.rect(0, 0, pageWidth, 40, "F");

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.setFont("helvetica", "bold");
    doc.text("CODESCOPE AI ANALYSIS", 20, 25);

    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.text(`REPORT ID: ${Math.random().toString(36).substr(2, 9).toUpperCase()}`, 20, 32);
    doc.text(`DATE: ${new Date().toLocaleDateString()}`, pageWidth - 60, 32);

    let yPos = 55;
    doc.setTextColor(15, 23, 42);
    doc.setFontSize(14);
    doc.text("EXECUTIVE METRICS", 20, yPos);

    yPos += 10;
    const colW = (pageWidth - 40) / 3;

    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text("QUALITY GRADE", 20, yPos);
    doc.setFontSize(12);
    doc.setTextColor(99, 102, 241);
    doc.setFont("helvetica", "bold");
    doc.text(cleanStr(result.quality_grade), 20, yPos + 7);

    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text("RISK LEVEL", 20 + colW, yPos);
    doc.setFontSize(12);
    const isHighRisk = result.risk.toLowerCase().includes("high");
    doc.setTextColor(isHighRisk ? 220 : 16, isHighRisk ? 38 : 185, isHighRisk ? 38 : 129);
    doc.text(cleanStr(result.risk), 20 + colW, yPos + 7);

    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text("COMPLEXITY", 20 + (colW * 2), yPos);
    doc.setFontSize(12);
    doc.setTextColor(34, 211, 238);
    doc.text(cleanStr(result.time_complexity), 20 + (colW * 2), yPos + 7);

    yPos += 25;
    doc.setDrawColor(226, 232, 240);
    doc.line(20, yPos, pageWidth - 20, yPos);

    yPos += 15;
    doc.setTextColor(15, 23, 42);
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("AI OBSERVATIONS", 20, yPos);

    yPos += 10;
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(71, 85, 105);

    result.explanations.forEach((obs: string) => {
      const splitText = doc.splitTextToSize(`> ${cleanStr(obs)}`, pageWidth - 40);
      if (yPos + 20 > 280) { doc.addPage(); yPos = 20; }
      doc.text(splitText, 20, yPos);
      yPos += (splitText.length * 6) + 4;
    });

    yPos += 10;
    autoTable(doc, {
      startY: yPos,
      head: [["FUNCTION NAME", "LINE", "SCORE", "REMARKS"]],
      body: result.functions.map((f: any) => [
        cleanStr(f.name),
        f.line,
        f.complexity,
        f.complexity > 5 ? "NEEDS REFACTOR" : "OPTIMIZED"
      ]),
      styles: { fontSize: 9, cellPadding: 5 },
      headStyles: { fillColor: [15, 23, 42], textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [249, 250, 251] },
      margin: { left: 20, right: 20 }
    });

    doc.save(`Analysis_Report_${new Date().getTime()}.pdf`);
  }

  async function loadHistory() {
    try {
      const res = await fetch(`${API_BASE}/history`);
      const data = await res.json();
      setHistory(data);
      setIsHistoryOpen(true);
    } catch (e) { console.error("Backend not connected"); }
  }

  const ChartContent = ({ height = 200, data = [] }: { height?: number, data?: any[] }) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: COLORS.textMuted, fontSize: 10 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: COLORS.textMuted, fontSize: 10 }} />
        <Tooltip cursor={{ fill: '#ffffff0a' }} contentStyle={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: '12px' }} />
        <Bar
          dataKey="complexity"
          radius={[6, 6, 0, 0]}
          barSize={40}
          onClick={(data: any) => {
            if (data && data.payload && data.payload.line) {
              handleFunctionClick(data.payload.line);
            }
          }}
          style={{ cursor: 'pointer' }}
        >
          {data.map((entry: any, index: number) => (
            <Cell key={index} fill={entry.complexity > 5 ? COLORS.danger : COLORS.primary} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  const StatsCards = () => (
    <>
      <div className="card"><p style={{ color: COLORS.textMuted, fontSize: "1rem", fontWeight: 700, marginBottom: "14px", letterSpacing: "0.05em" }}>RISK ASSESSMENT</p>{badge(result.risk)}</div>
      <div className="card">
        <p style={{ color: COLORS.textMuted, fontSize: "1rem", fontWeight: 700, marginBottom: "14px", letterSpacing: "0.05em" }}>CONFIDENCE</p>
        <b style={{ fontSize: "1.6rem", fontWeight: 800, color: result.confidence >= 80 ? "#10b981" : result.confidence >= 60 ? "#facc15" : COLORS.danger }}>
          {result.confidence}%
        </b>
      </div>
      <div className="card"><p style={{ color: COLORS.textMuted, fontSize: "1rem", fontWeight: 700, marginBottom: "14px", letterSpacing: "0.05em" }}>OVERALL GRADE</p>{badge(result.quality_grade)}</div>
      <div className="card"><p style={{ color: COLORS.textMuted, fontSize: "1rem", fontWeight: 700, marginBottom: "14px", letterSpacing: "0.05em" }}>COMPLEXITY</p><b style={{ color: COLORS.accent, fontSize: "1.1rem" }}>{result.time_complexity}</b></div>
    </>
  );

  // ── NEW: Monaco language id lookup ────────────────────────────────────────
  const monacoLanguage = LANGUAGES.find(l => l.value === language)?.monacoId ?? "plaintext";
  // ────────────────────────────────────────────────────────────────────────

  return (
    <div className="app">
      {/* ================= TOPBAR ================= */}
      <nav className="topbar">
        <div onClick={() => setIsSearchVisible(!isSearchVisible)} className="brand">
          <img src={logoImg} alt="Logo" style={{ width: 42, height: 42, borderRadius: "10px", objectFit: "contain" }} />
          <span className="brand-title">
            AI Based Code Complexity and Risk Prediction System Using Machine Learning
          </span>
        </div>

        <div className="topbar-center" />

        <div className="topbar-actions">
          <span className="topbar-byline">
            By <b style={{ color: COLORS.textMain }}>Aniruddha Sonawane</b>
          </span>
          <a href="https://github.com/Aniruddha-Sonawane" target="_blank" className="pill-link">
            <img src={githubLogo} alt="GitHub" style={{ width: 18, height: 18 }} />
            GitHub
          </a>
          <a href="https://www.linkedin.com/in/AniruddhaSonawane1" target="_blank" className="pill-link">
            <img src={linkedinLogo} alt="LinkedIn" style={{ width: 18, height: 18 }} />
            LinkedIn
          </a>
        </div>
      </nav>

      {isSearchVisible && (
        <>
          <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "transparent", zIndex: 1001 }} onClick={() => setIsSearchVisible(false)} />
          <div style={{ position: "fixed", top: "10px", left: "50%", transform: "translateX(-18.75%) translateY(12.5%)", width: "min(920px, 92vw)", zIndex: 1002 }}>
            <input autoFocus type="text" placeholder="Filter functions..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="search-input" style={{ width: "100%" }} />
          </div>
        </>
      )}

      {loading && (
        <div className="loading-overlay" role="status" aria-live="polite" aria-label="Analyzing">
          <div className="loading-spinner" />
          <div className="loading-text">Analyzing...</div>
        </div>
      )}

      <main className="main">
        <div className="layout">

          {/* LEFT SIDE */}
          <div>
            <div className={`editor-and-stats ${isEditorExpanded ? "expanded" : "collapsed"}`}>
              <div className="card editor-card">

                {/* ── NEW: Language selector bar ──────────────────────────── */}
                <div style={{ display: "flex", gap: "8px", marginBottom: "10px", flexWrap: "wrap" }}>
                  {LANGUAGES.map((lang) => (
                    <button
                      key={lang.value}
                      onClick={() => handleLanguageChange(lang.value)}
                      style={{
                        padding: "5px 14px",
                        borderRadius: "20px",
                        border: `1px solid ${language === lang.value ? COLORS.primary : COLORS.border}`,
                        background: language === lang.value ? `${COLORS.primary}22` : "transparent",
                        color: language === lang.value ? COLORS.primary : COLORS.textMuted,
                        fontSize: "0.78rem",
                        fontWeight: language === lang.value ? 700 : 400,
                        cursor: "pointer",
                        transition: "all 0.15s"
                      }}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
                {/* ───────────────────────────────────────────────────────── */}

                <div className="editor-shell">
                  <Editor
                    height="420px"
                    // ── CHANGED: dynamic language ──────────────────────────
                    language={monacoLanguage}
                    // ───────────────────────────────────────────────────────
                    value={code}
                    theme="vs-dark"
                    onChange={(v) => setCode(v || "")}
                    onMount={(editor) => { editorRef.current = editor; }}
                  />
                </div>

                <div className="actions">
                  <button onClick={analyze} className="btn btn-primary">
                    {loading ? "Analyzing..." : "Analyze Now"}
                  </button>
                  <button onClick={loadHistory} className="btn btn-outline">History</button>
                  <button
                    onClick={() => setIsEditorExpanded(!isEditorExpanded)}
                    className="btn btn-ghost"
                    aria-label={isEditorExpanded ? "Minimize editor" : "Expand editor"}
                    title={isEditorExpanded ? "Minimize editor" : "Expand editor"}
                  >
                    {isEditorExpanded ? "Minimize" : "Expand"}
                  </button>
                  {result && <button onClick={downloadReport} className="btn btn-ghost">Download PDF</button>}
                </div>
              </div>

              {!isEditorExpanded && result && (
                <div className="stats-column">
                  <StatsCards />
                </div>
              )}
            </div>

            {isEditorExpanded && result && (
              <div className="stats-grid">
                <StatsCards />
              </div>
            )}
          </div>

          {/* RIGHT SIDE */}
          <div className="sidebar">
            {result && (
              <>
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">Complexity Graph</h3>
                    <button onClick={() => setIsGraphZoomOpen(true)} className="btn btn-link">Expand ↗</button>
                  </div>
                  <ChartContent height={220} data={filteredFunctions} />
                </div>

                <div className="card observations-card">
                  <h3 className="card-title">AI Observations</h3>
                  <ul className="observations">
                    {result.explanations.map((e: string, i: number) => <li key={i} style={{ marginBottom: "10px" }}>{e}</li>)}
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      {/* ================= MODALS ================= */}

      {/* HISTORY MODAL */}
      {isHistoryOpen && (
        <>
          <div style={overlayStyle} onClick={() => setIsHistoryOpen(false)} />
          <div style={modalStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "25px" }}>
              <h2 style={{ margin: 0 }}>Analysis History</h2>
              <button onClick={() => setIsHistoryOpen(false)} style={{ background: "transparent", border: "none", color: COLORS.textMuted, fontSize: "2rem", cursor: "pointer" }}>&times;</button>
            </div>
            <div style={{ overflowY: "auto", flex: 1, minHeight: 0, paddingRight: "8px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setCode(item.code);
                      setResult(item.result);
                      // ── NEW: restore language from history if stored ──────
                      if (item.language) setLanguage(item.language);
                      // ────────────────────────────────────────────────────
                      setIsHistoryOpen(false);
                    }}
                    style={{ padding: "20px", border: `1px solid ${COLORS.border}`, borderRadius: "16px", cursor: "pointer", background: "rgba(255,255,255,0.02)" }}
                  >
                    <b style={{ color: COLORS.primary }}>Session #{item.id}</b>
                    {/* ── NEW: show language badge in history ──────────────── */}
                    {item.language && (
                      <span style={{ marginLeft: "8px", fontSize: "0.7rem", color: COLORS.accent, background: `${COLORS.accent}15`, padding: "2px 8px", borderRadius: "10px", border: `1px solid ${COLORS.accent}33` }}>
                        {item.language}
                      </span>
                    )}
                    {/* ────────────────────────────────────────────────────── */}
                    <p style={{ color: COLORS.textMuted, fontSize: "0.85rem", marginTop: "8px", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                      <span style={{ color: riskColor(item.result.risk) }}>◉</span>
                      {item.result.risk}
                      <span style={{ color: item.result.confidence >= 80 ? "#10b981" : item.result.confidence >= 60 ? "#facc15" : COLORS.danger }}>◉</span>
                      {item.result.confidence}%
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* EXPANDED GRAPH MODAL */}
      {isGraphZoomOpen && (
        <>
          <div style={overlayStyle} onClick={() => setIsGraphZoomOpen(false)} />
          <div style={modalStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
              <h3 style={{ margin: 0, fontSize: "1.1rem", fontFamily: "'Outfit', sans-serif", color: COLORS.textMain }}>
                Complexity Analysis
              </h3>
              <button onClick={() => setIsGraphZoomOpen(false)} style={{ background: "transparent", border: "none", color: COLORS.textMuted, cursor: "pointer", fontSize: "1.2rem" }}>
                &times;
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "20px", flex: 1, overflow: "hidden" }}>
              <div style={{ background: "rgba(0,0,0,0.2)", borderRadius: "12px", padding: "10px", border: `1px solid ${COLORS.border}` }}>
                <ChartContent height={380} data={filteredFunctions} />
              </div>

              <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
                <h4 style={{ color: COLORS.textMuted, fontSize: "0.65rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "10px" }}>
                  Functions ({filteredFunctions.length})
                </h4>
                <div style={{ overflowY: "auto", flex: 1, paddingRight: "8px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {filteredFunctions.map((fn: any, idx: number) => (
                      <div
                        key={idx}
                        onClick={() => handleFunctionClick(fn.line)}
                        style={{ padding: "10px 14px", background: "rgba(255,255,255,0.02)", borderRadius: "8px", border: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
                      >
                        <span style={{ fontSize: "0.85rem", fontWeight: "500", color: COLORS.textMain, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {fn.name}
                        </span>
                        <span style={{ fontSize: "0.85rem", fontWeight: "bold", color: fn.complexity > 5 ? COLORS.danger : COLORS.accent }}>
                          {fn.complexity}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
