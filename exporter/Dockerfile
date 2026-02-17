FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY weather_exporter.py .
EXPOSE 8000
CMD ["python", "weather_exporter.py"]