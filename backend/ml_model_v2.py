import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Features:
# [threads, locks, queues, classes, loops, infinite_loops,
#  ifs, functions, asyncs, globals, mem_allocs, random_calls, loc]

X = np.array([
    # ---------------- LOW ----------------
    [0,0,0,1,1,0,1,2,0,0,0,0,40],
    [0,0,0,1,2,0,2,3,0,0,0,0,70],
    [0,0,0,2,3,0,3,5,0,0,0,0,120],

    # ---------------- MEDIUM ----------------
    [1,1,0,3,4,1,5,8,0,1,0,1,180],
    [1,2,0,4,5,1,7,10,1,2,1,2,250],
    [2,2,0,5,6,1,9,12,1,3,1,2,300],

    # ---------------- HIGH ----------------
    [2,3,1,6,8,2,12,15,1,4,2,3,350],
    [3,3,1,7,10,2,14,18,2,6,3,4,450],
    [4,4,2,8,12,3,18,22,2,8,4,6,600],
    [5,5,3,10,15,4,25,30,3,10,6,8,900],
])

y = np.array([
    0,0,0,
    1,1,1,
    2,2,2,2
])

# ---------------- Train / Test Split ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

# ---------------- Evaluation ----------------
pred = model.predict(X_test)
acc = accuracy_score(y_test, pred)
print("✅ Model accuracy:", round(acc * 100, 2), "%")

# ---------------- Save ----------------
joblib.dump(model, "risk_model_v2.pkl")
print("✅ Model saved as risk_model_v2.pkl")
