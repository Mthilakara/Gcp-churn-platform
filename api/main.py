from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import logging
import json
import time
import uuid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("churn-api")



# Load trained model once when the API starts
MODEL_PATH = "ml/churn_model.joblib"
model = joblib.load(MODEL_PATH)

app = FastAPI(title="Churn Prediction API", version="1.0")


class ChurnFeatures(BaseModel):
    gender: str
    senior_citizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    monthly_charges: float
    total_charges: float | None = None  # allow null


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(features: ChurnFeatures):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        X = pd.DataFrame([features.model_dump()])
        churn_prob = float(model.predict_proba(X)[:, 1][0])
        churn_pred = 1 if churn_prob >= 0.5 else 0

        latency_ms = round((time.time() - start_time) * 1000, 2)

        log_payload = {
            "event": "prediction_success",
            "request_id": request_id,
            "churn_probability": churn_prob,
            "churn_prediction": churn_pred,
            "latency_ms": latency_ms,
            "model_version": "v1",
            "service": "churn-api"
        }

        # 🔑 THIS LINE MAKES jsonPayload
        print(json.dumps(log_payload))

        return {
            "request_id": request_id,
            "churn_probability": churn_prob,
            "churn_prediction": churn_pred
        }

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)

        error_payload = {
            "event": "prediction_error",
            "request_id": request_id,
            "error": str(e),
            "latency_ms": latency_ms,
            "service": "churn-api"
        }

        print(json.dumps(error_payload))
        raise