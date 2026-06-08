# Stage 1: dependency builder
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime
FROM python:3.11-slim
WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN mkdir -p data/uploads data/chroma_db

EXPOSE 8000

CMD ["python", "main.py"]
