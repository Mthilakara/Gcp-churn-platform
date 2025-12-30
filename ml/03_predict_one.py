import joblib
from google.cloud import bigquery

PROJECT_ID = "gcp-churn-platform"
TABLE = "gcp-churn-platform.churn_analytics.customer_churn_clean_dbt"

# 1) Load 1 sample row from BigQuery (features only)
client = bigquery.Client(project=PROJECT_ID)

sql = f"""
SELECT
  customer_id,
  gender,
  senior_citizen,
  Partner,
  Dependents,
  tenure,
  PhoneService,
  MultipleLines,
  InternetService,
  OnlineSecurity,
  OnlineBackup,
  DeviceProtection,
  TechSupport,
  StreamingTV,
  StreamingMovies,
  Contract,
  PaperlessBilling,
  PaymentMethod,
  monthly_charges,
  total_charges
FROM `{TABLE}`
LIMIT 1
"""

row = client.query(sql).to_dataframe()
customer_id = row["customer_id"].iloc[0]
X = row.drop(columns=["customer_id"])

# 2) Load trained model
clf = joblib.load("ml/churn_model.joblib")

# 3) Predict churn probability
churn_prob = float(clf.predict_proba(X)[:, 1][0])

print(f"customer_id: {customer_id}")
print(f"churn_probability: {churn_prob:.4f}")
