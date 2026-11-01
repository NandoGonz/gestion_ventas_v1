FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /app appuser

COPY app ./app
USER appuser
EXPOSE 8000
CMD ["python", "-m", "app.run"]
