FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY static ./static
ENV DB_PATH=/app/data/cartel.db
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8000"]
