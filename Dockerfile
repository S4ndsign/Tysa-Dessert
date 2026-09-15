FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["sh", "-c", "gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT --workers 2"]
