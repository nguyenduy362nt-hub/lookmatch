# Build nhẹ (chỉ API + test, không có mô hình):   docker build -f api/Dockerfile -t lookmatch:light .
# Build đầy đủ (có CLIP để /search chạy thật):   docker build -f api/Dockerfile --build-arg INSTALL_ML=1 -t lookmatch .
FROM python:3.11-slim

ARG INSTALL_ML=0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOOKMATCH_DATA=/app/data \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app
COPY api/requirements.txt api/requirements.txt
COPY api/requirements-ml.txt api/requirements-ml.txt
RUN pip install --no-cache-dir -r api/requirements.txt \
 && if [ "$INSTALL_ML" = "1" ]; then \
      pip install --no-cache-dir -r api/requirements-ml.txt --extra-index-url https://download.pytorch.org/whl/cpu; \
    fi

COPY api api

# Chạy bằng người dùng thường (không phải root); không có bí mật nào trong image
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /app/data /app/.cache/huggingface \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
