import { useState, useMemo, useRef } from "react"; // 1. Imported useRef
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

const cardStyle: React.CSSProperties = {
  background: COLORS.card,
  padding: "20px",
  borderRadius: "16px",
  border: `1px solid ${COLORS.border}`,
  marginBottom: "20px",
};

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

export default function App() {
  // --- 2. Create Reference for Editor ---
  const editorRef = useRef<any>(null);

  const [code, setCode] = useState<string>(`def example():\n    for i in range(10):\n        if i % 2 == 0:\n            print(i)`);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  
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

  // --- 3. Function to handle jumping to code line ---
  const handleFunctionClick = (line: number) => {
    // If the modal is open, close it so we can see the editor
    setIsGraphZoomOpen(false);

    if (editorRef.current && line) {
      // Reveal the line in the center of the editor
      editorRef.current.revealLineInCenter(line);
      // Move cursor to that line
      editorRef.current.setPosition({ lineNumber: line, column: 1 });
      // Focus the editor
      editorRef.current.focus();
    }
  };
  
  async function analyze() {
    setLoading(true);
    // Simulating result for demo purposes if backend isn't running
    // Replace with your actual fetch if backend is live
    try {
        const res = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code })
        });
        const data = await res.json();
        setResult(data);
    } catch (e) {
        console.error("Backend not connected");
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
        const res = await fetch("http://127.0.0.1:8000/history");
        const data = await res.json();
        setHistory(data);
        setIsHistoryOpen(true);
    } catch(e) { console.error("Backend not connected"); }
  }

  // --- 4. Pass click handler to BarChart ---
  const ChartContent = ({ height = 200, data = [] }: { height?: number, data?: any[] }) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: COLORS.textMuted, fontSize: 10}} />
        <YAxis axisLine={false} tickLine={false} tick={{fill: COLORS.textMuted, fontSize: 10}} />
        <Tooltip cursor={{fill: '#ffffff0a'}} contentStyle={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: '12px' }} />
        <Bar 
          dataKey="complexity" 
          radius={[6, 6, 0, 0]} 
          barSize={40} 
          // FIX IS HERE: Type as 'any' and access 'payload.line'
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

  return (
    <div style={{ background: COLORS.bg, minHeight: "100vh", color: COLORS.textMain, fontFamily: "'Inter', sans-serif" }}>
      
      {/* ================= TOPBAR ================= */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 100, background: "rgba(2, 6, 23, 0.85)",
        backdropFilter: "blur(12px)", borderBottom: `1px solid ${COLORS.border}`,
        padding: "0 40px", height: "70px", display: "flex", alignItems: "center"
      }}>
        <div 
          onClick={() => setIsSearchVisible(!isSearchVisible)} 
          style={{ display: "flex", alignItems: "center", gap: "15px", cursor: "pointer" }}
        >
          <img src={logoImg} alt="Logo" style={{ width: 42, height: 42, borderRadius: "10px", objectFit: "contain" }} />
          <span style={{ 
            fontWeight: 800, 
            fontSize: "1.05rem", 
            letterSpacing: "0.05em", 
            whiteSpace: "nowrap",
            fontFamily: "'Outfit', sans-serif",
            background: `linear-gradient(to right, ${COLORS.textMain}, ${COLORS.textMuted})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent"
          }}>
          AI CODE COMPLEXITY & QUALITY ANALYZER
          </span>
        </div>

        <div style={{ flex: 1, display: "flex", justifyContent: "center", padding: "0 40px" }}>
          {isSearchVisible && (
            <input 
              autoFocus
              type="text"
              placeholder="Filter functions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: "100%", maxWidth: "450px", background: "rgba(15, 23, 42, 0.6)",
                border: `1px solid ${COLORS.primary}88`, borderRadius: "12px",
                padding: "10px 20px", color: "#fff", outline: "none", fontSize: "0.9rem"
              }}
            />
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
          <span style={{ fontSize: "0.85rem", color: COLORS.textMuted }}>
            By <b style={{ color: COLORS.textMain }}>Aniruddha Sonawane</b>
          </span>
          <a href="https://github.com" target="_blank" style={{ color: COLORS.textMain, textDecoration: "none", fontSize: "0.8rem", border: `1px solid ${COLORS.border}`, padding: "6px 14px", borderRadius: "8px" }}>GitHub</a>
          <a href="https://linkedin.com" target="_blank" style={{ color: COLORS.textMain, textDecoration: "none", fontSize: "0.8rem", border: `1px solid ${COLORS.border}`, padding: "6px 14px", borderRadius: "8px" }}>LinkedIn</a>
        </div>
      </nav>

      <main style={{ maxWidth: "1500px", margin: "0 auto", padding: "30px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "2.2fr 1fr", gap: "25px" }}>
          
          {/* LEFT SIDE */}
          <div>
            <div style={cardStyle}>
              <div style={{ borderRadius: "12px", overflow: "hidden", border: `1px solid ${COLORS.border}` }}>
                {/* 5. Attach Editor Ref via onMount */}
                <Editor 
                    height="420px" 
                    defaultLanguage="python" 
                    value={code} 
                    theme="vs-dark" 
                    onChange={(v) => setCode(v || "")} 
                    onMount={(editor) => { editorRef.current = editor; }} 
                />
              </div>
              <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
                <button onClick={analyze} style={{ background: COLORS.primary, color: "#fff", border: "none", padding: "12px 28px", borderRadius: "10px", fontWeight: "bold", cursor: "pointer" }}>
                  {loading ? "Analyzing..." : "Analyze Now"}
                </button>
                <button onClick={loadHistory} style={{ background: "transparent", color: COLORS.textMain, border: `1px solid ${COLORS.border}`, padding: "12px 28px", borderRadius: "10px", cursor: "pointer" }}>
                  📜 History
                </button>
                {result && <button onClick={downloadReport} style={{ background: "transparent", color: COLORS.textMuted, border: "none", cursor: "pointer", marginLeft: "auto" }}>Download PDF</button>}
              </div>
            </div>

            {result && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px" }}>
                <div style={cardStyle}><p style={{ color: COLORS.textMuted, fontSize: "0.75rem", fontWeight: "bold", marginBottom: "12px" }}>RISK ASSESSMENT</p>{badge(result.risk)}</div>
                <div style={cardStyle}><p style={{ color: COLORS.textMuted, fontSize: "0.75rem", fontWeight: "bold", marginBottom: "12px" }}>OVERALL GRADE</p>{badge(result.quality_grade)}</div>
                <div style={cardStyle}><p style={{ color: COLORS.textMuted, fontSize: "0.75rem", fontWeight: "bold", marginBottom: "12px" }}>COMPLEXITY</p><b style={{ color: COLORS.accent, fontSize: "1.1rem" }}>{result.time_complexity}</b></div>
              </div>
            )}
          </div>

          {/* RIGHT SIDE */}
          <div style={{ position: "sticky", top: "100px" }}>
            {result && (
              <>
                <div style={cardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                    <h3 style={{ fontSize: "0.9rem", color: COLORS.textMuted, margin: 0 }}>Complexity Graph</h3>
                    <button onClick={() => setIsGraphZoomOpen(true)} style={{ background: "transparent", border: "none", color: COLORS.accent, cursor: "pointer", fontSize: "0.8rem" }}>Expand ↗</button>
                  </div>
                  <ChartContent height={220} data={filteredFunctions} />
                </div>

                <div style={cardStyle}>
                  <h3 style={{ fontSize: "0.9rem", color: COLORS.textMuted, marginBottom: "15px" }}>AI Observations</h3>
                  <ul style={{ paddingLeft: "1.2rem", color: COLORS.textMuted, fontSize: "0.85rem", lineHeight: "1.7" }}>
                    {result.explanations.map((e: string, i: number) => <li key={i} style={{ marginBottom: "10px" }}>{e}</li>)}
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      {/* ================= MODALS ================= */}
      
      {/* HISTORY MODAL (UNTOUCHED) */}
      {isHistoryOpen && (
        <>
          <div style={overlayStyle} onClick={() => setIsHistoryOpen(false)} />
          <div style={modalStyle}>
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "25px" }}>
              <h2 style={{ margin: 0 }}>Analysis History</h2>
              <button onClick={() => setIsHistoryOpen(false)} style={{ background: "transparent", border: "none", color: COLORS.textMuted, fontSize: "2rem", cursor: "pointer" }}>&times;</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              {history.map((item) => (
                <div key={item.id} onClick={() => { setCode(item.code); setResult(item.result); setIsHistoryOpen(false); }} 
                     style={{ padding: "20px", border: `1px solid ${COLORS.border}`, borderRadius: "16px", cursor: "pointer", background: "rgba(255,255,255,0.02)" }}>
                  <b style={{ color: COLORS.primary }}>Session #{item.id}</b>
                  <p style={{ color: COLORS.textMuted, fontSize: "0.85rem", marginTop: "8px" }}>{item.result.functions.length} functions found • {item.result.quality_grade} Grade</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* EXPANDED GRAPH MODAL */}
      {isGraphZoomOpen && (
  <>
    <div style={overlayStyle} onClick={() => setIsGraphZoomOpen(false)} />
    <div style={modalStyle}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
        <h3 style={{ margin: 0, fontSize: "1.1rem", fontFamily: "'Outfit', sans-serif", color: COLORS.textMain }}>
          Complexity Analysis
        </h3>
        <button 
          onClick={() => setIsGraphZoomOpen(false)} 
          style={{ background: "transparent", border: "none", color: COLORS.textMuted, cursor: "pointer", fontSize: "1.2rem" }}
        >
          &times;
        </button>
      </div>

      {/* CONTENT GRID */}
      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "20px", flex: 1, overflow: "hidden" }}>
        
        {/* LEFT: GRAPH AREA */}
        <div style={{ background: "rgba(0,0,0,0.2)", borderRadius: "12px", padding: "10px", border: `1px solid ${COLORS.border}` }}>
          <ChartContent height={380} data={filteredFunctions} />
        </div>

        {/* RIGHT: LIST AREA (SCROLLABLE) */}
        <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <h4 style={{ color: COLORS.textMuted, fontSize: "0.65rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "10px" }}>
            Functions ({filteredFunctions.length})
          </h4>
          
          <div style={{ overflowY: "auto", flex: 1, paddingRight: "8px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {filteredFunctions.map((fn: any, idx: number) => (
                <div 
                  key={idx} 
                  // 6. Attach Click Handler to List Items
                  onClick={() => handleFunctionClick(fn.line)}
                  style={{ 
                    padding: "10px 14px", 
                    background: "rgba(255,255,255,0.02)", 
                    borderRadius: "8px", 
                    border: `1px solid ${COLORS.border}`,
                    display: "flex", 
                    justifyContent: "space-between", 
                    alignItems: "center",
                    cursor: "pointer" // Make it look clickable
                  }}
                  // Optional hover effect could be added here via CSS class
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
                >
                  <span style={{ fontSize: "0.85rem", fontWeight: "500", color: COLORS.textMain, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {fn.name}
                  </span>
                  <span style={{ 
                    fontSize: "0.85rem", 
                    fontWeight: "bold", 
                    color: fn.complexity > 5 ? COLORS.danger : COLORS.accent 
                  }}>
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