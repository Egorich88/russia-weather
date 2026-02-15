#!/usr/bin/env python3
from prometheus_client import start_http_server, Gauge
import time
import random

cities = ['Moscow', 'SPb', 'Novosibirsk', 'Vladivostok', 'Kaliningrad']
temp = Gauge('weather_temp', 'Temperature', ['city'])

print("Starting Weather Exporter...")
start_http_server(8000)

while True:
    for city in cities:
        t = round(random.uniform(-20, 25), 1)
        temp.labels(city=city).set(t)
        print(f"{city}: {t}°C")
    time.sleep(15)
