FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=WARNING

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4042

CMD ["gunicorn", "-k", "gunicorn_worker.ProductionUvicornWorker", "-c", "gunicorn_conf.py", "main:app"]
