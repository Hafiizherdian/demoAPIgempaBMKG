# Gunakan base image Ubuntu 20.04
FROM ubuntu:20.04

# Set environment variable untuk menghindari prompt interaktif
ENV DEBIAN_FRONTEND=noninteractive

# Ganti repository dengan mirror yang lebih cepat
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirror.rackspace.com/ubuntu/|g' /etc/apt/sources.list

# Install Python, pip, dan OpenJDK
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.9 \
        python3-pip \
        openjdk-11-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip dan set mirror PyPI yang cepat
RUN pip install --upgrade pip && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Set WORKDIR
WORKDIR /app

# Copy requirements.txt dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy aplikasi ke container
COPY . .

# Expose port untuk Streamlit
EXPOSE 8501

# Command untuk menjalankan Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]