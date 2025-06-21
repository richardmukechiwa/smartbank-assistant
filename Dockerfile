# Use official Python 3.12 slim image
FROM python:3.12-slim

# Install dependencies to build SQLite and other tools
RUN apt-get update && apt-get install -y \
    wget build-essential libsqlite3-dev gcc make \
    && apt-get clean

# Download, build, and install SQLite >= 3.35
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3440000.tar.gz && \
    tar -xzf sqlite-autoconf-3440000.tar.gz && \
    cd sqlite-autoconf-3440000 && \
    ./configure && make && make install && \
    cd .. && rm -rf sqlite-autoconf-3440000*

# Ensure Python uses the new SQLite
ENV LD_LIBRARY_PATH="/usr/local/lib"
ENV PATH="/usr/local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Install required Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
