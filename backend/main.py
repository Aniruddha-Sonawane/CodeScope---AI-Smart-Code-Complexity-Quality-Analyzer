from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from radon.complexity import cc_visit
from database import SessionLocal, Analysis
import joblib
import numpy as np

from quality_engine import calculate_quality_score
from feature_extractor import extract_features
from complexity_analyzer import estimate_complexity

# ----------------------------
# App Init
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://ai-code-complexity-analyzer-ml.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Load ML Model
# ----------------------------
model = joblib.load("risk_model_v2.pkl")

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
    # Extract Complexity Metrics
    # ------------------------
    for r in results:
        item = {
            "name": r.name,
            "complexity": r.complexity,
            "line": r.lineno
        }
        functions.append(item)

        if r.complexity >= 10:
            warnings.append(
                f"⚠️ Function '{r.name}' is very complex (CC={r.complexity}). Consider refactoring."
            )
        elif r.complexity >= 5:
            warnings.append(
                f"⚠️ Function '{r.name}' is moderately complex (CC={r.complexity}). Review logic."
            )

    # ------------------------
    # AST Feature Extraction
    # ------------------------
    features = extract_features(req.code)
    print("🧠 EXTRACTED FEATURES:", features)

    (
        threads,
        locks,
        queues,
        classes,
        loops,
        infinite_loops,
        ifs,
        funcs,
        asyncs,
        globals_,
        mem_allocs,
        random_calls,
        loc
    ) = features

    feature_vector = np.array([features])

    # ------------------------
    # ML Prediction + Confidence
    # ------------------------
    proba = model.predict_proba(feature_vector)[0]
    prediction = int(np.argmax(proba))
    confidence = float(np.max(proba))

    risk_map = {
        0: "Low Risk 🟢",
        1: "Medium Risk 🟡",
        2: "High Risk 🔴"
    }

    ml_risk = risk_map[prediction]
    final_risk = ml_risk

    # ------------------------
    # Hybrid Safety Rules
    # ------------------------
    explanations = []
    danger_score = 0

    if mem_allocs > 0:
        danger_score += 2
        explanations.append("Memory allocation detected (possible leak)")

    if globals_ >= 3:
        danger_score += 2
        explanations.append("Many global mutable variables")

    if asyncs > 0 and threads > 0:
        danger_score += 2
        explanations.append("Async mixed with threading")

    if random_calls >= 3:
        danger_score += 2
        explanations.append("Frequent random behavior detected")

    if locks >= 2 and threads >= 3:
        danger_score += 1
        explanations.append("Multiple locks with many threads")

    if infinite_loops >= 2 and random_calls >= 2:
        danger_score += 2
        explanations.append("Unstable infinite loops detected")

    if infinite_loops >= 3:
        danger_score += 1
        explanations.append("Heavy infinite looping")

    if threads >= 5:
        danger_score += 1
        explanations.append("High thread count")

    # Baseline
    if infinite_loops > 0:
        baseline_risk = "Medium Risk 🟡"
        explanations.append("Infinite loop detected")
    elif threads >= 1:
        baseline_risk = "Medium Risk 🟡"
        explanations.append("Concurrent system detected")
    else:
        baseline_risk = ml_risk

    # Final Risk
    if danger_score >= 4:
        final_risk = "High Risk 🔴"
    elif danger_score >= 2:
        final_risk = "Medium Risk 🟡"
    else:
        final_risk = baseline_risk

    if final_risk != ml_risk:
        explanations.append(f"ML predicted {ml_risk}, adjusted by safety rules")

    # ------------------------
    # Time Complexity
    # ------------------------
    time_complexity = estimate_complexity(req.code)

    # ------------------------
    # Code Quality Score
    # ------------------------
    complexities = [f["complexity"] for f in functions]
    avg_complexity = (
        sum(complexities) / len(complexities)
        if complexities else 0
    )

    quality_score, quality_grade, quality_reasons = calculate_quality_score(
        avg_complexity=avg_complexity,
        warning_count=len(warnings),
        loc=loc,
        globals_=globals_,
        random_calls=random_calls,
        mem_allocs=mem_allocs,
        threads=threads,
        locks=locks,
        infinite_loops=infinite_loops,
        danger_score=danger_score
    )

    # ------------------------
    # Save to Database
    # ------------------------
    db = SessionLocal()
    record = Analysis(
        code=req.code,
        result={
            "functions": functions,
            "warnings": warnings,
            "risk": final_risk,
            "ml_risk": ml_risk,
            "confidence": round(confidence * 100, 2),
            "features": features,
            "explanations": explanations,
            "danger_score": danger_score,
            "time_complexity": time_complexity,
            "quality_score": quality_score,
            "quality_grade": quality_grade,
            "quality_reasons": quality_reasons
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
        "risk": final_risk,
        "ml_risk": ml_risk,
        "confidence": round(confidence * 100, 2),
        "features": features,
        "explanations": explanations,
        "danger_score": danger_score,
        "time_complexity": time_complexity,
        "quality_score": quality_score,
        "quality_grade": quality_grade,
        "quality_reasons": quality_reasons
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
