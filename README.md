# GCP Churn Platform — DataOps + MLOps + DevOps (dbt, FastAPI, Cloud Run, Jenkins)

An end-to-end “pet project” that demonstrates how modern teams ship data + ML products using **DataOps + MLOps + DevOps** patterns on Google Cloud.

This platform turns raw churn data into ML-ready features (dbt), trains a model (scikit-learn), serves predictions via an API (FastAPI), deploys serverlessly (Cloud Run), and adds observability using structured logging + logs-based metrics + dashboards. CI/CD is automated with Jenkins running on a GCE VM.

---

## What this project demonstrates

### DataOps
- Raw data lands in **GCS**
- Loaded into **BigQuery (raw table)**
- Transformed & tested with **dbt** into clean ML-ready tables

### MLOps (practical / lightweight)
- Offline training script produces a **versioned model artifact**
- Model is used consistently by the serving API

### DevOps
- API containerized with **Docker**
- Image stored in **Artifact Registry**
- Deployed to **Cloud Run**
- Automated build/deploy via **Jenkins pipeline**

### Observability
- API emits **structured JSON logs** (jsonPayload in Cloud Logging)
- **Logs-based metric** counts successful predictions
- Dashboards & alerts can be built in **Cloud Monitoring**

---

## High-level architecture (flow)

**Data path**

**Serving + ops**

**CI/CD**

![Project Architecture](images/Project_diagram.png)

---

## Repo structure (typical)

- `api/` — FastAPI app (loads model, exposes `/predict`, writes JSON logs)
- `ml/` — training code + model artifact output
- `churn_dbt/` — dbt project (sources, models, tests)
- `logs/` — notes/examples for structured logging & metrics (optional)
- `Dockerfile` — container build instructions
- `requirements.txt` — pinned Python deps :contentReference[oaicite:1]{index=1}

---

## Prerequisites

### Local machine
- Python 3.10+ (recommended)
- Git
- Docker (optional for local container builds)
- dbt BigQuery adapter:
  - `dbt-bigquery`

### Google Cloud
- A GCP project (example: `gcp-churn-platform`)
- Billing enabled
- `gcloud` CLI installed + authenticated

---

# Phase 0 — Prepare your machine & cloud account

## 0.1 Clone repo & create a virtual environment
```bash
git clone https://github.com/Mthilakara/Gcp-churn-platform.git
cd Gcp-churn-platform

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## 0.2 Authenticate & set your GCP project
```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud config set run/region us-central1
```
## 0.3 Enable required GCP APIs
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com
  
```

# Phase 1 — Data ingestion (CSV → GCS → BigQuery)

## 1.1Create a GCS bucket (raw landing zone)
```bash
export PROJECT_ID="<YOUR_PROJECT_ID>"
export REGION="us-central1"
export BUCKET="${PROJECT_ID}-churn-raw"

gsutil mb -l ${REGION} gs://${BUCKET}
```
## 1.2 Upload dataset to GCS

```bash
gsutil cp path/to/churn.csv gs://${BUCKET}/raw/
```
## 1.3 Create BigQuery dataset + load raw table
```bash
bq --location=${REGION} mk -d ${PROJECT_ID}:churn

bq load \
  --source_format=CSV \
  --autodetect \
  ${PROJECT_ID}:churn.customer_churn_raw \
  gs://${BUCKET}/raw/churn.csv
```
# Phase 2 — Transform with dbt (BigQuery)

This repo includes a dbt project under churn_dbt/. The exact models depend on your implementation, but the pattern is:
- source() points to customer_churn_raw
- staging model cleans types/columns
- final model is ML-ready
- tests enforce assumptions (not_null, unique, accepted_values, etc.)

## 2.1 Install dbt BigQuery adapter
```bash
pip install dbt-bigquery
```
## 2.2 Configure dbt profile
```bash
~/.dbt/profiles.yml
```
Example skeleton:
```bash
churn_dbt:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: <YOUR_PROJECT_ID>
      dataset: churn
      threads: 4
      location: us-central1
```
## 2.3 Run dbt models + tests
```bash
cd churn_dbt
dbt debug
dbt run
dbt test
```
# Phase 3 — Train the churn model (offline)

The training step reads the dbt-clean BigQuery table (or exported data) and produces a serialized model artifact (joblib).

Typical flow:

-  Extract features from BigQuery clean table
- Train + evaluate.
- Save churn_model.joblib (and optionally a model version tag)

Example command (adjust to your training script):
```bash
python ml/train.py
```
# Phase 4 — Serve predictions via FastAPI

##4.1 Run locally (dev mode)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```
Then open:

- Swagger UI: http://localhost:8080/docs
- Prediction endpoint: POST http://localhost:8080/predict

# Phase 5 — Containerize & deploy (Artifact Registry → Cloud Run)

## 5.1 Create Artifact Registry repo (Docker)\

```bash
export PROJECT_ID="<YOUR_PROJECT_ID>"
export REGION="us-central1"
export REPO="churn-repo"

gcloud artifacts repositories create ${REPO} \
  --repository-format=docker \
  --location=${REGION} \
  --description="Docker repo for churn-api"
```
## 5.2 Configure Docker auth for Artifact Registry
```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev -q
```
## 5.3 Build & push the image

```bash
export SERVICE="churn-api"
export TAG="$(date +%Y%m%d-%H%M%S)"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:${TAG}"

docker build -t "${IMAGE}" .
docker push "${IMAGE}"
```

## 5.4 Deploy to Cloud Run
```bash
gcloud run deploy ${SERVICE} \
  --image "${IMAGE}" \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --port 8080
```
After deploy, Cloud Run will provide a public HTTPS URL.

# Phase 6 — Structured logging → Logs-based metric → Monitoring

## 6.1 Why structured logging?
Instead of writing plain text logs, the API emits JSON logs so Cloud Logging stores them as jsonPayload.

That makes it easy to:
- filter by jsonPayload.event="prediction_success"
- build metrics from logs
- alert on error spikes or latency

## 6.2 Logs-based metric (counter)
Create a Logs-based metric in Cloud Logging:

Type: Counter

Filter example:
```bash
resource.type="cloud_run_revision"
resource.labels.service_name="churn-api"
jsonPayload.event="prediction_success"
```
Then visualize it in Cloud Monitoring:

- Metrics Explorer → your custom metric → chart
- Optional: alert if predictions drop to 0 unexpectedly or error rate increases

# Phase 7 — CI/CD with Jenkins on GCE (Option 1)
This project uses Jenkins for learning and “real-world-ish” CI/CD.

## 7.1 Jenkins pipeline goals
On every push to GitHub (main branch):

- Checkout code

- Run unit checks (optional)

- Build Docker image

- Push image to Artifact Registry

- Deploy new revision to Cloud Run

## 7.2 Jenkins requirements (GCE VM)

- Docker installed

- Jenkins user allowed to run Docker

- gcloud installed and authenticated via VM service account

VM service account needs IAM roles:

- Artifact Registry Writer

- Cloud Run Admin (or Cloud Run Developer)

- Service Account User (if deploying with a runtime SA)

- A Jenkinsfile can encode the above steps end-to-end.

# Tech stack

- Storage: GCS

- Warehouse: BigQuery

- Transformations: dbt

- ML: Python + scikit-learn + joblib

- API: FastAPI + Uvicorn GitHub

- Container: Docker

- Registry: Artifact Registry

- Serverless: Cloud Run

- Observability: Cloud Logging + Logs-based Metrics + Cloud Monitoring

- CI/CD: Jenkins on GCE VM












































```bash

```
