FROM python:3.11-slim

WORKDIR /app

# dependências do oracle
RUN apt-get update && apt-get install -y \
    libaio1 unzip && \
    rm -rf /var/lib/apt/lists/*

# copiar instant client
COPY instantclient/instantclient_19_30 /opt/oracle/instantclient_19_30

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_30/

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "app.main"]