FROM python:3.12-slim

WORKDIR /extract-text

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-rus \
    libreoffice \
    unrar-free \
    p7zip-full \
    fonts-unifont \
    fonts-dejavu-core \
    libgtk-3-0 \
    libgbm1 \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY third_party/extract-text/requirements.txt /extract-text/requirements.txt
RUN pip install --no-cache-dir -r /extract-text/requirements.txt

RUN python -m playwright install chromium

COPY third_party/extract-text/app /extract-text/app

ENV EXTRACT_TEXT_HOST=0.0.0.0 \
    EXTRACT_TEXT_PORT=7555

EXPOSE 7555

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7555"]
