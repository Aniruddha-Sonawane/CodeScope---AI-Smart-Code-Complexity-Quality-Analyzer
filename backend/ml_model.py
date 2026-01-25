import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

# ----------------------------------
# Dummy Training Dataset (synthetic)
# ----------------------------------
# Features:
# [avg_complexity, max_complexity, function_count, warning_count, loc]

X = np.array([
    [2, 3, 2, 0, 40],    # Low risk
    [3, 5, 3, 1, 80],    # Low risk
    [5, 7, 4, 2, 150],   # Medium
    [6, 9, 5, 3, 220],   # Medium
    [9, 15, 7, 5, 400],  # High
    [12, 18, 10, 7, 700] # High
])

# Labels: 0 = Low, 1 = Medium, 2 = High
y = np.array([0, 0, 1, 1, 2, 2])

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

joblib.dump(model, "risk_model.pkl")

print("✅ ML model trained and saved")
