# Python 3.11 Slim rasmi asosida
FROM python:3.11-slim

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_ENV=production

# Ishchi papkani yaratish
WORKDIR /app

# Tizim paketlarini yangilash
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Talab qilinadigan kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Loyiha kodlarini nusxalash
COPY . .

# Portni ochish
EXPOSE 5000

# Serverni Gunicorn orqali ishga tushirish
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:application"]
