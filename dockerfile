# Use a "slim" image to keep things small and fast
FROM python:3.11-slim


# Run the backend from its own directory so local imports resolve correctly.
WORKDIR /app/backend

# Copy backend dependencies and install them.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code.
COPY backend/ .

# Cloud Run provides PORT at runtime; default to 8080 locally.
ENV PORT=8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]