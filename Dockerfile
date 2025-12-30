FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code + model file
COPY api ./api
COPY ml ./ml

# Cloud Run listens on $PORT
ENV PORT=8080

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]
