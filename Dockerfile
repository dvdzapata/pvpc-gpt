FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY server.py /app/server.py

RUN pip install fastapi uvicorn requests mcp-server

EXPOSE 8080

CMD ["python", "server.py"]
