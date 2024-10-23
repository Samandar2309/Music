# Python versiyasini tanlang
FROM python:3.11-slim

# Kerakli tizim kutubxonalarini o'rnating (agar kerak bo'lsa)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    python3-venv \  # Bu qatorda venv ni qo'shing
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ishchi katalogini yaratish
WORKDIR /Music

# requirements.txt faylini ko'chiring
COPY requirements.txt .

# Virtual muhitni yaratish va kutubxonalarni o'rnatish
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt || { echo "Installation failed"; exit 1; }

# Dasturni ko'chirish
COPY . .

# Kontainer ishga tushganda qaysi komandani bajarsin
CMD ["/opt/venv/bin/python", "spofity.py"]
