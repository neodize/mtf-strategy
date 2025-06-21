FROM python:3.9-slim

WORKDIR /app

# Preinstall NumPy and TA-Lib from wheels
RUN pip install --upgrade pip
RUN pip install numpy==1.24.4 TA-Lib==0.4.28

# Install other requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY trading_bot.py .
COPY config/config.yaml .

CMD ["python", "trading_bot.py"]
