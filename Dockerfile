FROM python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home experience
COPY . .
RUN mkdir -p /app/data /app/backups && chown -R experience:experience /app
USER 10001:10001
ENV EXPERIENCE_CONFIG=/app/config/deployment.json EXPERIENCE_DATABASE=/app/data/knowledge.sqlite PYTHONUNBUFFERED=1
EXPOSE 18110
CMD ["gunicorn","--bind","0.0.0.0:18110","--workers","1","--threads","4","--timeout","60","app:create_app()"]
