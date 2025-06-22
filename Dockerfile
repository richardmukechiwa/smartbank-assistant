# Use official Python 3.12 image
FROM python:3.12-slim-bullseye

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LD_LIBRARY_PATH=/usr/local/lib \
    PATH="/usr/local/bin:$PATH"

# Set working directory
WORKDIR /app

# Install system dependencies and tools to build SQLite
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libsqlite3-dev \
    gcc \
    make \
    && apt-get clean

# Upgrade SQLite to 3.44.0 (you can change this if needed)
RUN wget https://www.sqlite.org/2025/sqlite-autoconf-3500100.tar.gz && \
    tar -xzf sqlite-autoconf-3500100.tar.gz && \
    cd sqlite-autoconf-3500100 && \
    ./configure && make && make install && \
    cd .. && rm -rf sqlite-autoconf-3500100*


# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all app code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
