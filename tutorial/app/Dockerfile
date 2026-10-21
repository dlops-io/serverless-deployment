FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY pyproject.toml ./
COPY translation_demo ./translation_demo
COPY examples ./examples
RUN pip install --no-cache-dir --no-deps . && useradd --uid 1000 --create-home app
USER app
EXPOSE 8080
CMD ["python", "-m", "translation_demo", "serve"]
