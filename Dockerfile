FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt

COPY . /app

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

CMD ["sh", "-c", "python init_db.py && exec gunicorn --workers 3 --threads 2 --timeout 60 --bind 0.0.0.0:8000 app:app"]
