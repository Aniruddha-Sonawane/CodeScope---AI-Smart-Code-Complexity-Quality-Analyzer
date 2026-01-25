import { useState } from "react";
import Editor from "@monaco-editor/react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

// --- Theme Constants ---
const COLORS = {
  bg: "#020617",
  card: "#0f172a",
  border: "#1e293b",
  textMain: "#f8fafc",
  textMuted: "#94a3b8",
  primary: "#6366f1",
  primaryHover: "#4f46e5",
  accent: "#06b6d4",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444"
};

const cardStyle: React.CSSProperties = {
  background: COLORS.card,
  padding: "20px",
  borderRadius: "12px",
  border: `1px solid ${COLORS.border}`,
  marginBottom: "20px",
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 20px",
  borderRadius: "8px",
  border: "none",
  fontWeight: "600",
  cursor: "pointer",
  transition: "all 0.2s ease",
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
};

// --- Refined Badge Component ---
function badge(text: string) {
  let bgColor = "rgba(148, 163, 184, 0.1)";
  let textColor = COLORS.textMuted;

  if (text.includes("Low") || text.includes("Excellent")) {
    bgColor = "rgba(16, 185, 129, 0.15)";
    textColor = COLORS.success;
  } else if (text.includes("Medium") || text.includes("Fair") || text.includes("Good")) {
    bgColor = "rgba(245, 158, 11, 0.15)";
    textColor = COLORS.warning;
  } else if (text.includes("High") || text.includes("Poor")) {
    bgColor = "rgba(239, 68, 68, 0.15)";
    textColor = COLORS.danger;
  }

  return (
    <span style={{
      background: bgColor,
      color: textColor,
      padding: "4px 12px",
      borderRadius: "20px",
      fontSize: "0.75rem",
      fontWeight: "bold",
      textTransform: "uppercase",
      border: `1px solid ${textColor}33`,
      marginLeft: "10px"
    }}>
      {text}
    </span>
  );
}

export default function App() {
  const [code, setCode] = useState<string>(
    `def example():\n    for i in range(10):\n        if i % 2 == 0:\n            print(i)`
  );
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);

  async function analyze() {
    setLoading(true);
    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code })
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  }

  function downloadReport() {
    if (!result) return;
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text("CodeScope Analysis Report", 14, 20);
    autoTable(doc, {
      startY: 30,
      head: [["Function", "Complexity", "Line"]],
      body: result.functions.map((f: any) => [f.name, f.complexity, f.line]),
    });
    let y = (doc as any).lastAutoTable.finalY + 15;
    doc.text(`Risk: ${result.risk}`, 14, y); y += 8;
    doc.text(`Confidence: ${result.confidence}%`, 14, y); y += 8;
    doc.text(`Time Complexity: ${result.time_complexity}`, 14, y); y += 8;
    doc.text(`Quality: ${result.quality_score}/100 (${result.quality_grade})`, 14, y);
    doc.save("codescope-report.pdf");
  }

  async function loadHistory() {
    const res = await fetch("http://127.0.0.1:8000/history");
    const data = await res.json();
    setHistory(data);
  }

  function loadFromHistory(item: any) {
    setCode(item.code);
    setResult(item.result);
  }

  return (
    <div style={{
      padding: "40px",
      background: COLORS.bg,
      minHeight: "100vh",
      color: COLORS.textMain,
      fontFamily: "'Inter', system-ui, sans-serif",
      boxSizing: "border-box"
    }}>
      
      {/* Header */}
      <header style={{ marginBottom: "40px" }}>
        <h1 style={{ 
          fontSize: "2rem", 
          fontWeight: "800", 
          margin: 0, 
          background: `linear-gradient(to right, ${COLORS.primary}, ${COLORS.accent})`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          CodeScope AI <span style={{ fontWeight: "300", color: COLORS.textMuted, WebkitTextFillColor: COLORS.textMuted }}>| Analyzer</span>
        </h1>
        <p style={{ color: COLORS.textMuted, marginTop: "8px" }}>Deep complexity analysis and quality scoring powered by AI.</p>
      </header>

      <div style={{
        display: "grid",
        gridTemplateColumns: "1.8fr 1fr",
        gap: "24px",
        alignItems: "start"
      }}>
        
        {/* LEFT COLUMN */}
        <div>
          {/* Editor Card */}
          <div style={cardStyle}>
            <div style={{ borderRadius: "8px", overflow: "hidden", border: `1px solid ${COLORS.border}` }}>
              <Editor
                height="320px"
                defaultLanguage="python"
                value={code}
                onChange={(value) => setCode(value || "")}
                theme="vs-dark"
                options={{ fontSize: 14, minimap: { enabled: false }, padding: { top: 16 } }}
              />
            </div>

            <div style={{ marginTop: "20px", display: "flex", gap: "12px" }}>
              <button 
                onClick={analyze} 
                style={{ ...buttonStyle, background: COLORS.primary, color: "white" }}
                disabled={loading}
              >
                {loading ? "Analyzing..." : "🚀 Run Analysis"}
              </button>
              {result && (
                <button onClick={downloadReport} style={{ ...buttonStyle, background: COLORS.border, color: COLORS.textMain }}>
                  📄 Export PDF
                </button>
              )}
              <button onClick={loadHistory} style={{ ...buttonStyle, background: "transparent", color: COLORS.textMuted, border: `1px solid ${COLORS.border}` }}>
                📜 View History
              </button>
            </div>
          </div>

          {/* Results Grid */}
          {result && (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "16px",
              marginBottom: "24px"
            }}>
              <div style={cardStyle}>
                <div style={{ color: COLORS.textMuted, fontSize: "0.8rem", marginBottom: "8px" }}>Risk Level</div>
                <div style={{ fontSize: "1.2rem", fontWeight: "bold", display: "flex", alignItems: "center" }}>
                   {badge(result.risk)}
                </div>
                <div style={{ fontSize: "0.75rem", color: COLORS.textMuted, marginTop: "10px" }}>Confidence: {result.confidence}%</div>
              </div>

              <div style={cardStyle}>
                <div style={{ color: COLORS.textMuted, fontSize: "0.8rem", marginBottom: "8px" }}>Quality Grade</div>
                <div style={{ fontSize: "1.2rem", fontWeight: "bold" }}>
                   {badge(result.quality_grade)}
                </div>
                <div style={{ fontSize: "0.75rem", color: COLORS.textMuted, marginTop: "10px" }}>Score: {result.quality_score}/100</div>
              </div>

              <div style={cardStyle}>
                <div style={{ color: COLORS.textMuted, fontSize: "0.8rem", marginBottom: "8px" }}>Time Complexity</div>
                <div style={{ fontSize: "1.1rem", fontWeight: "bold", color: COLORS.accent }}>{result.time_complexity}</div>
                <div style={{ fontSize: "0.75rem", color: COLORS.textMuted, marginTop: "10px" }}>Predicted Scale</div>
              </div>
            </div>
          )}

          {/* Chart Section */}
          {result && (
            <div style={cardStyle}>
              <h3 style={{ fontSize: "1rem", marginBottom: "20px", color: COLORS.textMuted }}>Complexity per Function</h3>
              <div style={{ height: 250 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={result.functions}>
                    <XAxis dataKey="name" stroke={COLORS.textMuted} fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke={COLORS.textMuted} fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: "8px" }}
                      cursor={{ fill: COLORS.border }}
                    />
                    <Bar dataKey="complexity" radius={[4, 4, 0, 0]}>
                      {result.functions.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.complexity > 5 ? COLORS.danger : COLORS.primary} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ position: "sticky", top: 40 }}>
          {result && (
            <div style={cardStyle}>
              <h3 style={{ fontSize: "1rem", marginBottom: "16px" }}>🔍 Observations</h3>
              <ul style={{ paddingLeft: "18px", color: COLORS.textMuted, lineHeight: "1.6", fontSize: "0.9rem" }}>
                {result.explanations.map((e: string, i: number) => (
                  <li key={i} style={{ marginBottom: "8px" }}>{e}</li>
                ))}
              </ul>

              <hr style={{ border: "none", borderTop: `1px solid ${COLORS.border}`, margin: "20px 0" }} />

              <h3 style={{ fontSize: "1rem", marginBottom: "16px" }}>📊 Breakdown</h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                <thead>
                  <tr style={{ color: COLORS.textMuted, textAlign: "left" }}>
                    <th style={{ padding: "8px" }}>Function</th>
                    <th style={{ padding: "8px", textAlign: "center" }}>Cyclomatic</th>
                    <th style={{ padding: "8px", textAlign: "center" }}>Line</th>
                  </tr>
                </thead>
                <tbody>
                  {result.functions.map((fn: any, idx: number) => (
                    <tr key={idx} style={{ borderTop: `1px solid ${COLORS.border}` }}>
                      <td style={{ padding: "12px 8px", fontWeight: "600" }}>{fn.name}</td>
                      <td style={{ padding: "12px 8px", textAlign: "center", color: COLORS.accent }}>{fn.complexity}</td>
                      <td style={{ padding: "12px 8px", textAlign: "center" }}>{fn.line}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* History Section */}
          {history.length > 0 && (
            <div style={cardStyle}>
              <h3 style={{ fontSize: "1rem", marginBottom: "16px" }}>📜 Recent Audits</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => loadFromHistory(item)}
                    style={{
                      padding: "10px",
                      borderRadius: "8px",
                      background: COLORS.bg,
                      cursor: "pointer",
                      border: `1px solid ${COLORS.border}`,
                      fontSize: "0.8rem",
                      transition: "transform 0.1s"
                    }}
                  >
                    <div style={{ fontWeight: "bold", marginBottom: "4px" }}>Audit #{item.id}</div>
                    <div style={{ color: COLORS.textMuted }}>
                      {item.result.functions.length} functions detected • {item.result.warnings.length} warnings
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}