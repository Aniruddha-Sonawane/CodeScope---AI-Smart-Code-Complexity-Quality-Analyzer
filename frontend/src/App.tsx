import { useState } from "react";
import Editor from "@monaco-editor/react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

const cardStyle: React.CSSProperties = {
  background: "#111",
  padding: 16,
  borderRadius: 10,
  boxShadow: "0 0 10px rgba(0,0,0,0.4)",
  marginBottom: 16
};

function badge(text: string) {
  let color = "#999";
  if (text.includes("Low")) color = "#22c55e";
  if (text.includes("Medium")) color = "#facc15";
  if (text.includes("High")) color = "#ef4444";
  if (text.includes("Excellent")) color = "#22c55e";
  if (text.includes("Good")) color = "#3b82f6";
  if (text.includes("Fair")) color = "#f97316";
  if (text.includes("Poor")) color = "#ef4444";

  return (
    <span
      style={{
        background: color,
        color: "#000",
        padding: "4px 10px",
        borderRadius: 12,
        fontWeight: "bold",
        marginLeft: 8
      }}
    >
      {text}
    </span>
  );
}

export default function App() {
  const [code, setCode] = useState<string>(
`def example():
    for i in range(10):
        if i % 2 == 0:
            print(i)
`
  );

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);

  // ------------------------
  // Analyze Code
  // ------------------------
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

  // ------------------------
  // Download PDF
  // ------------------------
  function downloadReport() {
    if (!result) return;

    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text("CodeScope Analysis Report", 14, 20);

    autoTable(doc, {
      startY: 30,
      head: [["Function", "Complexity", "Line"]],
      body: result.functions.map((f: any) => [
        f.name,
        f.complexity,
        f.line
      ]),
    });

    let y = (doc as any).lastAutoTable.finalY + 15;

    doc.text(`Risk: ${result.risk}`, 14, y); y += 8;
    doc.text(`Confidence: ${result.confidence}%`, 14, y); y += 8;
    doc.text(`Time Complexity: ${result.time_complexity}`, 14, y); y += 8;
    doc.text(
      `Quality: ${result.quality_score}/100 (${result.quality_grade})`,
      14,
      y
    );

    doc.save("codescope-report.pdf");
  }

  // ------------------------
  // History
  // ------------------------
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
    <div
      style={{
        padding: 20,
        background: "#0f172a",
        minHeight: "100vh",
        width: "100vw",
        color: "#fff",
        boxSizing: "border-box"
      }}
    >
      <h1 style={{ fontSize: 25, marginLeft: 8, marginTop: -8, marginBottom: 9, textAlign: "left" }}>
         AI SMART CODE COMPLEXITY & QUALITY ANALYZER
      </h1>

      {/* ================= TWO COLUMN LAYOUT ================= */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2.2fr 1fr",
          gap: 20,
          alignItems: "start"
        }}
      >
        {/* =====================================================
            LEFT COLUMN
        ====================================================== */}
        <div>
          {/* ================= EDITOR ================= */}
          <div style={cardStyle}>
            <Editor
              height="280px"
              defaultLanguage="python"
              value={code}
              onChange={(value) => setCode(value || "")}
              theme="vs-dark"
            />

            <div style={{ marginTop: 12 }}>
              <button onClick={analyze}>
                {loading ? "Analyzing..." : "Analyze"}
              </button>

              {result && (
                <button onClick={downloadReport} style={{ marginLeft: 10 }}>
                  📄 Download Report
                </button>
              )}

              <button onClick={loadHistory} style={{ marginLeft: 10 }}>
                📜 History
              </button>
            </div>
          </div>

          {/* ================= DASHBOARD ================= */}
          {result && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: 16
              }}
            >
              {/* Risk */}
              <div style={cardStyle}>
                <h3>🤖 Risk</h3>
                {badge(result.risk)}
                <p>Confidence: {result.confidence}%</p>
              </div>

              {/* Quality */}
              <div style={cardStyle}>
                <h3>🏆 Code Quality</h3>
                {badge(result.quality_grade)}
                <p>Score: {result.quality_score}/100</p>
              </div>

              {/* Time */}
              <div style={cardStyle}>
                <h3>⏱️ Time Complexity</h3>
                <p>{result.time_complexity}</p>
              </div>
            </div>
          )}

          {/* ================= EXPLANATIONS ================= */}
          {result?.explanations?.length > 0 && (
            <div style={cardStyle}>
              <h3>🧠 Why this result?</h3>
              <ul>
                {result.explanations.map((e: string, i: number) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {/* ================= CHART ================= */}
          {result && (
            <div style={cardStyle}>
              <h3>📈 Complexity Chart</h3>
              <div style={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={result.functions}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="complexity" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ================= HISTORY ================= */}
          {history.length > 0 && (
            <div style={cardStyle}>
              <h3>📜 History</h3>
              <table width="100%" cellPadding={6}>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Functions</th>
                    <th>Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr
                      key={item.id}
                      style={{ cursor: "pointer" }}
                      onClick={() => loadFromHistory(item)}
                    >
                      <td>{item.id}</td>
                      <td align="center">
                        {item.result.functions.length}
                      </td>
                      <td align="center">
                        {item.result.warnings.length}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* =====================================================
            RIGHT COLUMN — COMPLEXITY TABLE
        ====================================================== */}
        <div style={{ position: "sticky", top: 20 }}>
          {result && (
            <div style={cardStyle}>
              <h3>📊 Complexity Table</h3>

              <table width="100%" cellPadding={6}>
                <thead>
                  <tr>
                    <th align="left">Function</th>
                    <th>Complexity</th>
                    <th>Line</th>
                  </tr>
                </thead>
                <tbody>
                  {result.functions.map((fn: any, idx: number) => (
                    <tr key={idx}>
                      <td>{fn.name}</td>
                      <td align="center">{fn.complexity}</td>
                      <td align="center">{fn.line}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
