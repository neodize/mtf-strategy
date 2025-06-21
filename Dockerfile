# ----------  BASE IMAGE WITH PRE‑BUILT WHEEL SUPPORT ----------
FROM python:3.9-slim      # wheel exists for CPython 3.9

WORKDIR /app

# ----------  WHEEL‑FRIENDLY DEPENDENCIES ----------
RUN pip install --upgrade pip
RUN pip install numpy==1.24.4 TA-Lib==0.4.28   # <— installs wheel, no GCC

# ----------  REST OF PYTHON DEPENDENCIES ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------  APP CODE ----------
COPY trading_bot.py .
COPY config/config.yaml ./config.yaml   # adjust path if needed

CMD ["python", "trading_bot.py"]
