from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from radon.complexity import cc_visit

app = FastAPI()

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],     # IMPORTANT
    allow_headers=["*"],     # IMPORTANT
)

class CodeRequest(BaseModel):
    code: str

@app.post("/analyze")
def analyze_code(req: CodeRequest):
    results = cc_visit(req.code)
    data = []
    for r in results:
        data.append({
            "name": r.name,
            "complexity": r.complexity,
            "line": r.lineno
        })
    return {"functions": data}
