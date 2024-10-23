# Python versiyasini tanlang
FROM python:3.11.0

# Kerakli tizim kutubxonalarini o'rnating
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ishchi katalogini yaratish
WORKDIR /Music

# requirements.txt faylini ko'chiring
COPY requirements.txt .

# Virtual muhitni yaratish
RUN python -m venv /opt/venv

# pip ni yangilang
RUN /opt/venv/bin/python -m pip install --upgrade pip

# Kutubxonalarni o'rnatish
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Dasturni ko'chirish
COPY . .

# Kontainer ishga tushganda qaysi komandani bajarsin
CMD ["/opt/venv/bin/python", "spofity.py"]
