FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib from source with proper version
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Update pip first
RUN pip install --upgrade pip

# Copy requirements and install Python packages
COPY requirements.txt .

# Install Python packages with specific flags for TA-Lib
RUN pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir TA-Lib==0.4.25 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY trading_bot.py .
COPY config.yaml .
COPY .env .

CMD ["python", "trading_bot.py"]