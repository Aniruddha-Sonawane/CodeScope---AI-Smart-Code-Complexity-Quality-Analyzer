from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from radon.complexity import cc_visit
from database import SessionLocal, Analysis

import joblib
import numpy as np

# ----------------------------
# App Init
# ----------------------------
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
# Load ML Model (ONCE)
# ----------------------------
model = joblib.load("risk_model.pkl")

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

    # ------------------------
    # Extract Metrics
    # ------------------------
    for r in results:
        item = {
            "name": r.name,
            "complexity": r.complexity,
            "line": r.lineno
        }
        functions.append(item)

        # Rule engine
        if r.complexity >= 10:
            warnings.append(
                f"⚠️ Function '{r.name}' is very complex (CC={r.complexity}). Consider refactoring."
            )
        elif r.complexity >= 5:
            warnings.append(
                f"⚠️ Function '{r.name}' is moderately complex (CC={r.complexity}). Review logic."
            )

    # ------------------------
    # ML Feature Engineering
    # ------------------------
    complexities = [f["complexity"] for f in functions]

    avg_complexity = sum(complexities) / len(complexities) if complexities else 0
    max_complexity = max(complexities) if complexities else 0
    function_count = len(functions)
    warning_count = len(warnings)
    loc = len(req.code.splitlines())

    features = np.array([[
        avg_complexity,
        max_complexity,
        function_count,
        warning_count,
        loc
    ]])

    # ------------------------
    # ML Prediction
    # ------------------------
    prediction = model.predict(features)[0]

    risk_map = {
        0: "Low Risk 🟢",
        1: "Medium Risk 🟡",
        2: "High Risk 🔴"
    }

    risk_level = risk_map[int(prediction)]

    # ------------------------
    # Save to Database
    # ------------------------
    db = SessionLocal()
    record = Analysis(
        code=req.code,
        result={
            "functions": functions,
            "warnings": warnings,
            "risk": risk_level
        }
    )
    db.add(record)
    db.commit()
    db.close()

    # ------------------------
    # API Response
    # ------------------------
    return {
        "functions": functions,
        "warnings": warnings,
        "risk": risk_level
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
