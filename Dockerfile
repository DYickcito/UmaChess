FROM python:3.12-slim
WORKDIR /app
COPY requirements-web.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt
COPY servidor_web.py ./
COPY config.js ./
COPY web ./web
COPY assets ./assets
ENV PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["sh", "-c", "uvicorn servidor_web:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
