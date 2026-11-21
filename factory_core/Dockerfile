# factory_core image. Build from the repository root (see docker-compose.yml): the service finds the root by its folders.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /repo/factory_core
COPY factory_core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY contracts /repo/contracts
COPY model_estate /repo/model_estate
COPY factory_core /repo/factory_core
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
