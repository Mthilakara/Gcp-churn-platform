import joblib
from google.cloud import bigquery
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score

PROJECT_ID = "gcp-churn-platform"
TABLE = "gcp-churn-platform.churn_analytics.customer_churn_clean_dbt"

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
  total_charges,
  churn_flag
FROM `{TABLE}`
"""
df = client.query(sql).to_dataframe()

y = df["churn_flag"].astype(int)
X = df.drop(columns=["churn_flag", "customer_id"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

numeric_features = ["senior_citizen", "tenure", "monthly_charges", "total_charges"]
categorical_features = [c for c in X.columns if c not in numeric_features]

preprocess = ColumnTransformer(
    transformers=[
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric_features),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical_features),
    ]
)

clf = Pipeline(steps=[
    ("preprocess", preprocess),
    ("model", LogisticRegression(max_iter=2000)),
])

clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:, 1]

print("\nClassification report:\n")
print(classification_report(y_test, y_pred))

print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

joblib.dump(clf, "ml/churn_model.joblib")
print("\nSaved model to: ml/churn_model.joblib")
