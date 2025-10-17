# Base image
FROM python:3.11-slim

# create workspace directory
WORKDIR /app

# install dependencies
# update system packages and install the essential library
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# copy requirements and install packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy the application code
COPY . .

# set default port
EXPOSE 8001

ENV PYTHONPATH=/app
# execute FastAPI (keep '--reload' in development environment)
CMD ["python", "-m", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

