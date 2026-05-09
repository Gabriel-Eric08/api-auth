FROM python:3.12-slim

# Evita arquivos .pyc e melhora logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema (opcional)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro para cache
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY . .

# Porta do Cloud Run
ENV PORT=8080

# Gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 app:app