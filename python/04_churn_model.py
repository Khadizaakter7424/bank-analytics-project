"""
STEP 4 - CHURN PREDICTION MODEL
===============================
Trains two simple models to predict which customers will churn:
  * Logistic Regression  (simple baseline)
  * Random Forest        (stronger, also tells us which features matter)

Then it gives EVERY customer a churn probability and a risk level
(High / Medium / Low). Power BI and SQL use that file.

Input : data/processed/customers_clean.csv
Output: data/processed/churn_scores.csv       (customer_id, probability, risk level)
        data/processed/customers_scored.csv   (customers + scores, use this in Power BI)
        data/processed/model_metrics.csv
        images/feature_importance.png

Run:
    python python/04_churn_model.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_FILE = BASE_DIR / "data" / "processed" / "customers_clean.csv"
SCORES_FILE = BASE_DIR / "data" / "processed" / "churn_scores.csv"
SCORED_FILE = BASE_DIR / "data" / "processed" / "customers_scored.csv"
METRICS_FILE = BASE_DIR / "data" / "processed" / "model_metrics.csv"
IMG_DIR = BASE_DIR / "images"
IMG_DIR.mkdir(exist_ok=True)

if not CUSTOMERS_FILE.exists():
    raise SystemExit("Run python/01_clean_data.py first.")

df = pd.read_csv(CUSTOMERS_FILE)

# ---------------------------------------------------------------
# 1. Choose features (X) and the target (y)
#    Text columns (geography, gender) become 0/1 columns with get_dummies.
# ---------------------------------------------------------------
feature_cols = [
    "credit_score", "geography", "gender", "age", "tenure", "balance",
    "num_of_products", "has_cr_card", "is_active_member", "estimated_salary",
]
X = pd.get_dummies(df[feature_cols], columns=["geography", "gender"], drop_first=True)
y = df["exited"]

# ---------------------------------------------------------------
# 2. Split: 80% to learn from, 20% hidden to test fairly
#    stratify=y keeps the same churn share in both parts.
# ---------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------------------------------------------------------
# 3. Define the models
#    class_weight="balanced" tells the model that churners are rare but important.
# ---------------------------------------------------------------
models = {
    "Logistic Regression": make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=20,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1,
    ),
}

# ---------------------------------------------------------------
# 4. Train and evaluate
# ---------------------------------------------------------------
rows = []
for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    rows.append({
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
    })
    print(f"\n{name}")
    print("Confusion matrix [[TN FP] [FN TP]]:")
    print(confusion_matrix(y_test, pred))

metrics = pd.DataFrame(rows).round(3)
metrics.to_csv(METRICS_FILE, index=False)
print("\nModel comparison (higher is better):")
print(metrics.to_string(index=False))
print("\nHow to read it: recall = share of real churners we caught; "
      "precision = share of our 'will churn' alerts that were right.")

# ---------------------------------------------------------------
# 5. Which features matter most? (Random Forest)
# ---------------------------------------------------------------
forest = models["Random Forest"]
importance = pd.Series(forest.feature_importances_, index=X.columns).sort_values()
top = importance.tail(10)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(top.index, top.values, color="#2F6B9A", height=0.55)
for i, v in enumerate(top.values):
    ax.text(v + 0.003, i, f"{v:.2f}", va="center", fontsize=9, color="#1F2937")
ax.set_title("What drives churn? Top features (Random Forest)", loc="left",
             fontsize=13, fontweight="bold", color="#1F2937")
ax.xaxis.grid(True, color="#E5E7EB")
ax.set_axisbelow(True)
for side in ["top", "right", "bottom"]:
    ax.spines[side].set_visible(False)
ax.tick_params(colors="#6B7280", length=0)
fig.tight_layout()
fig.savefig(IMG_DIR / "feature_importance.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------
# 6. Score ALL customers
#    cross_val_predict gives each customer a probability from a model that
#    did NOT see that customer during training (fair, no cheating).
# ---------------------------------------------------------------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
prob_all = cross_val_predict(forest, X, y, cv=cv, method="predict_proba")[:, 1]

scores = pd.DataFrame({
    "customer_id": df["customer_id"],
    "churn_probability": prob_all.round(4),
})
scores["risk_level"] = pd.cut(
    scores["churn_probability"],
    bins=[-0.001, 0.40, 0.65, 1.0],
    labels=["Low", "Medium", "High"],
).astype(str)

scores.to_csv(SCORES_FILE, index=False)

# One combined file (customer details + risk score) = the easiest file for Power BI
df.merge(scores, on="customer_id").to_csv(SCORED_FILE, index=False)

print("\nRisk level distribution:")
print(scores["risk_level"].value_counts())
print("\nSaved:", SCORES_FILE)
