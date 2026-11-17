FROM python:3.12-slim
#PYTHONDONTWRITEBYTECODE  Purpose: Prevents Python from generating .pyc bytecode cache files.
#PYTHONUNBUFFERED         Purpose: Ensures Python prints output immediately instead of buffering it.
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1          

WORKDIR /srv

# dependencies first so this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# keep the package folder: main.py imports "from app import rules"
COPY app/ ./app/
COPY .env .

EXPOSE 8000

# --env-file loads SENTINEL_API_KEY / SENTINEL_RULES_CONFIG from the copied .env
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--env-file", ".env"]
