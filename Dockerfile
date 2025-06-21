FROM python:3.9-slim        # wheel is built for CPython 3.9

WORKDIR /app

# ---------- Python deps (TA‑Lib wheel first) ----------
RUN pip install --upgrade pip \
 && pip install TA-Lib==0.4.28      \
               numpy==1.24.4        # last NumPy before the 2.0 ABI break

# ---------- Copy project ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY trading_bot.py .
COPY config/config.yaml ./config.yaml     # adjust if you renamed path

CMD ["python", "trading_bot.py"]
