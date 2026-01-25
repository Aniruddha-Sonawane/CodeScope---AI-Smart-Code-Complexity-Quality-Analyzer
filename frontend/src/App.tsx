import { useState } from "react";
import "./App.css";

function App() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function analyze() {
    if (!code.trim()) return alert("Paste some code first!");

    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ code })
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert("Backend not running or CORS error.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>🚀 CodeScope Analyzer</h1>

      <textarea
        placeholder="Paste your code here..."
        rows={12}
        style={{ width: "100%", fontFamily: "monospace" }}
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />

      <br /><br />

      <button onClick={analyze} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze"}
      </button>

      <pre style={{ marginTop: 20 }}>
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
}

export default App;
