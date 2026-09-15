FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:3000", "--workers", "2"]
