FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    MPLBACKEND=Agg \
    TZ=Asia/Seoul \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# OpenMP is required by LightGBM; tzdata keeps scheduler time in KST.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Install the CPU wheel explicitly before resolving the remaining requirements.
RUN python -m pip install --no-deps "torch==2.8.0" --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements.txt \
    && python -m pip check

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY configs/ ./configs/
COPY taglist/ ./taglist/

RUN mkdir -p /app/models /app/runs /app/logs \
    && python -c "import lightgbm, xgboost" \
    && python scripts/harness/schedule.py --help > /dev/null

ENTRYPOINT ["python", "scripts/harness/schedule.py"]
CMD ["--help"]
