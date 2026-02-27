FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY web /app/web
COPY run.py /app/run.py

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000

EXPOSE 8000

CMD ["python", "run.py"]
