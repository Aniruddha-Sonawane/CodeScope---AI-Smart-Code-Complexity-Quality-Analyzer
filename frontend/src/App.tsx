import { useState } from "react";
import Editor from "@monaco-editor/react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer
} from "recharts";

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

  const chartData = result?.functions || [];

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

    <button
      onClick={analyze}
      style={{ marginTop: 10, padding: "8px 16px" }}
    >
      {loading ? "Analyzing..." : "Analyze"}
    </button>

    {result && (
      <>
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

        {/* ✅ WARNINGS SECTION */}
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
  </div>
);

}

export default App;
