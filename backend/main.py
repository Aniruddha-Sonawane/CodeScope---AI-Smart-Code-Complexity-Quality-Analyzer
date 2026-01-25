from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from radon.complexity import cc_visit

from database import SessionLocal, Analysis

app = FastAPI()

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Request Model
# ----------------------------
class CodeRequest(BaseModel):
    code: str


# ----------------------------
# Analyze Endpoint
# ----------------------------
@app.post("/analyze")
def analyze_code(req: CodeRequest):
    results = cc_visit(req.code)

    functions = []
    warnings = []

    for r in results:
        item = {
            "name": r.name,
            "complexity": r.complexity,
            "line": r.lineno
        }
        functions.append(item)

        # ✅ Rule engine
        if r.complexity >= 10:
            warnings.append(
                f"⚠️ Function '{r.name}' is very complex (CC={r.complexity}). Consider refactoring."
            )
        elif r.complexity >= 5:
            warnings.append(
                f"⚠️ Function '{r.name}' is moderately complex (CC={r.complexity}). Review logic."
            )

    # ✅ Save to database (ONLY ONCE per request)
    db = SessionLocal()
    record = Analysis(
        code=req.code,
        result={
            "functions": functions,
            "warnings": warnings
        }
    )
    db.add(record)
    db.commit()
    db.close()

    return {
        "functions": functions,
        "warnings": warnings
    }


# ----------------------------
# History Endpoint
# ----------------------------
@app.get("/history")
def get_history():
    db = SessionLocal()
    records = db.query(Analysis).order_by(Analysis.id.desc()).limit(20).all()
    db.close()

    return [
        {
            "id": r.id,
            "code": r.code,
            "result": r.result
        }
        for r in records
    ]
