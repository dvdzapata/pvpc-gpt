FROM python:3.11-slim

# Evita problemas de buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copia el servidor MCP
COPY server.py /app/server.py

# Si tienes dependencias, descomenta:
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "server.py"]
