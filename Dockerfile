FROM python:3.9-slim
# Set working directory
WORKDIR /app
# Install system dependencies for TA-Lib
# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
# Install TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib*
# Install TA-Lib from source with proper version
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
# Set library path
ENV LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH
# Update pip first
RUN pip install --upgrade pip
# Copy requirements first for better caching
# Copy requirements and install Python packages
COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Install Python packages with specific flags for TA-Lib
RUN pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir TA-Lib==0.4.25 && \
    pip install --no-cache-dir -r requirements.txt
# Copy application code
# Copy application files
COPY trading_bot.py .
COPY config.yaml .
COPY .env .
# Create logs directory
RUN mkdir -p /app/logs
# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1
# Run the bot
CMD ["python", "trading_bot.py"]