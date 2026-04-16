FROM python:3.12-slim AS backend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p /app/data/uploads /app/data/exports

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM node:20-slim AS frontend

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ .
RUN npm run build


FROM python:3.12-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY --from=backend /app /app/backend
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=frontend /app/dist /app/frontend/dist

COPY nginx.conf /etc/nginx/sites-available/default

RUN mkdir -p /app/data/uploads /app/data/exports

WORKDIR /app/backend

EXPOSE 80

CMD ["sh", "-c", "uvicorn main:app --host 127.0.0.1 --port 8000 & nginx -g 'daemon off;'"]
