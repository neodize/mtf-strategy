FROM python:3.9-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    python3-dev \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
 && tar -xvzf ta-lib-0.4.0-src.tar.gz \
 && cd ta-lib && ./configure --prefix=/usr && make && make install \
 && cd .. && rm -rf ta-lib*

ENV LD_LIBRARY_PATH="/usr/lib:$LD_LIBRARY_PATH"

# Add TA-Lib headers to Python path
ENV TA_LIBRARY_PATH="/usr/lib"
ENV TA_INCLUDE_PATH="/usr/include"

# Copy requirements
COPY requirements.txt .

# Install pip packages (include numpy pinned)
RUN pip install --upgrade pip
RUN pip install numpy==1.24.4  # Pinned for TA-Lib compatibility
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY trading_bot.py .
COPY config.yaml .

CMD ["python", "trading_bot.py"]
