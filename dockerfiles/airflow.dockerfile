FROM apache/airflow:2.9.1-python3.12

USER root
# Cài đặt Java, Curl VÀ bổ sung các công cụ biên dịch (build-essential, python3-dev...) 
# để khắc phục lỗi khi pip install các thư viện C/C++
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    default-jre-headless \
    curl \
    build-essential \
    python3-dev \
    libpq-dev \
    libkrb5-dev \
    pkg-config \
    default-libmysqlclient-dev \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cấu hình JAVA_HOME trỏ về bản Java mặc định của hệ thống
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
USER airflow

COPY dockerfiles/airflow.requirements.txt .
RUN pip install --no-cache-dir -r airflow.requirements.txt