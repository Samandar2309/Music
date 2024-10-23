FROM python:3.12-slim

# Ish joyini o'rnatish
WORKDIR /app

# Talab qilingan kutubxonalarni ko'chirish
COPY requirements.txt .

# PIP cache uchun katalogni yaratish
RUN mkdir -p /root/.cache/pip

# Virtual muhitni yaratish va kutubxonalarni o'rnatish
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Kod fayllarini ko'chirish
COPY . .

# Asosiy dastur faylini ishga tushirish
CMD ["/opt/venv/bin/python", "spofity.py"]
