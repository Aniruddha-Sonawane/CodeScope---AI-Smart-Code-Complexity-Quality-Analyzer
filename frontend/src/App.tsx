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

function App() {
  const [code, setCode] = useState<string>(
`def example():
    for i in range(10):
        if i % 2 == 0:
            print(i)

def second():
    for x in range(5):
        print(x)
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
  // Download PDF Report
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

    if (result.warnings && result.warnings.length > 0) {
      let y = (doc as any).lastAutoTable.finalY + 10;
      doc.text("Warnings:", 14, y);

      result.warnings.forEach((w: string) => {
        y += 8;
        doc.text(`- ${w}`, 14, y);
      });
    }

    // ✅ Include AI Risk in PDF
    if (result.risk) {
      const y = (doc as any).lastAutoTable.finalY + 40;
      doc.text(`AI Risk Prediction: ${result.risk}`, 14, y);
    }

    doc.save("codescope-report.pdf");
  }

  // ------------------------
  // Load History from Backend
  // ------------------------
  async function loadHistory() {
    const res = await fetch("http://127.0.0.1:8000/history");
    const data = await res.json();
    setHistory(data);
  }

  // ------------------------
  // Restore From History
  // ------------------------
  function loadFromHistory(item: any) {
    setCode(item.code);
    setResult(item.result);
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>🚀 CodeScope Analyzer</h1>

      <Editor
        height="300px"
        defaultLanguage="python"
        value={code}
        onChange={(value) => setCode(value || "")}
        theme="vs-dark"
      />

      <div style={{ marginTop: 10 }}>
        <button onClick={analyze} style={{ padding: "8px 16px" }}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>

        {result && (
          <button
            onClick={downloadReport}
            style={{ marginLeft: 10, padding: "8px 16px" }}
          >
            📄 Download Report
          </button>
        )}

        <button
          onClick={loadHistory}
          style={{ marginLeft: 10, padding: "8px 16px" }}
        >
          📜 Load History
        </button>
      </div>

      {result && (
        <>
          {/* ✅ AI Risk Display */}
          {result.risk && (
            <h2 style={{ marginTop: 20 }}>
              🤖 AI Risk Prediction: <span>{result.risk}</span>
            </h2>
          )}

          <h2>📊 Complexity Table</h2>

          <table border={1} cellPadding={8}>
            <thead>
              <tr>
                <th>Function</th>
                <th>Complexity</th>
                <th>Line</th>
              </tr>
            </thead>
            <tbody>
              {result.functions.map((fn: any, idx: number) => (
                <tr key={idx}>
                  <td>{fn.name}</td>
                  <td>{fn.complexity}</td>
                  <td>{fn.line}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {result.warnings && result.warnings.length > 0 && (
            <>
              <h2 style={{ color: "red" }}>⚠️ Code Warnings</h2>
              <ul>
                {result.warnings.map((w: string, idx: number) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </>
          )}

          <h2>📈 Complexity Chart</h2>

          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={result.functions}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="complexity" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {history.length > 0 && (
        <>
          <h2>📜 Analysis History</h2>

          <table border={1} cellPadding={6}>
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
                  <td>{item.result.functions.length}</td>
                  <td>{item.result.warnings.length}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p>👉 Click any row to restore analysis</p>
        </>
      )}
    </div>
  );
}

export default App;
