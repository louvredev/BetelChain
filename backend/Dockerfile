FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE $PORT

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

