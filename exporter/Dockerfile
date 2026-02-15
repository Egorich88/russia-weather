FROM python:3.9-slim
WORKDIR /app
RUN pip install prometheus-client
COPY weather_exporter.py .
EXPOSE 8000
CMD ["python", "weather_exporter.py"]
