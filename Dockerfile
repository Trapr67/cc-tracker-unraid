# --- Frontend build ---
FROM node:18-bullseye as frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Backend runtime ---
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential gcc libffi-dev libssl-dev && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend-build /app/frontend/build ./frontend_build

# Optional: include an icon (PNG) at /app/icon.png so Unraid can point to http://[IP]:[PORT:3535]/icon.png
# Add your icon file to unraid-template/cc-tracker.png or any path you prefer, then copy it:
#COPY unraid-template/cc-tracker.png ./icon.png

EXPOSE 3535
CMD ["gunicorn", "-b", "0.0.0.0:3535", "app:app", "--workers", "2", "--threads", "4"]

