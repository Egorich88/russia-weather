#!/usr/bin/env python3
import time
import requests
from prometheus_client import start_http_server, Gauge

# Словарь городов: название -> ID (найденные на Gismeteo)
CITY_IDS = {
    "Москва": 4368,
    "Санкт-Петербург": 4079,
    "Новосибирск": 4690,
    "Екатеринбург": 4517,
    "Казань": 4362,
    "Нижний Новгород": 4355,
    "Челябинск": 4515,
    "Омск": 3988,
    "Самара": 4618,
    "Ростов-на-Дону": 4601,
    "Уфа": 4520,
    "Красноярск": 4678,
    "Пермь": 4508,
    "Воронеж": 4586,
    "Волгоград": 4585,
    "Краснодар": 4526,
    "Саратов": 4620,
    "Тюмень": 4521,
    "Тольятти": 4623,
    "Ижевск": 4451,
    "Барнаул": 4647,
    "Ульяновск": 4625,
    "Иркутск": 4693,
    "Хабаровск": 4745,
    "Ярославль": 4372,
    "Владивосток": 4743,
    "Махачкала": 4467,
    "Томск": 4697,
    "Оренбург": 4511,
    "Кемерово": 4696,
    "Новокузнецк": 4695,
    "Рязань": 4357,
    "Астрахань": 4578,
    "Набережные Челны": 4463,
    "Пенза": 4605,
    "Липецк": 4353,
    "Киров": 4435,
    "Чебоксары": 4359,
    "Тула": 4361,
    "Калининград": 4236,
    "Курск": 4575,
    "Севастополь": 5146,
    "Сочи": 4528,
    "Симферополь": 5145,
    "Мурманск": 4123,
    "Архангельск": 4179,
    "Якутск": 4723,
    "Петропавловск-Камчатский": 4763,
    "Магадан": 4748,
    "Анадырь": 4776,
    "Южно-Сахалинск": 4754,
    "Комсомольск-на-Амуре": 4746,
    "Благовещенск": 4740,
    "Тында": 4744,
}

# Публичный эндпоинт Gismeteo (без токена)
BASE_URL = "https://www.gismeteo.com/api/v2/weather/current/{}"

# Метрики Prometheus
temperature_gauge = Gauge('weather_temp_celsius', 'Температура в городах России', ['city'])
humidity_gauge = Gauge('weather_humidity_percent', 'Влажность в городах России', ['city'])

def fetch_weather(city_name, city_id):
    url = BASE_URL.format(city_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.gismeteo.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Статус для {city_name}: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text[:200])
            return None, None
        data = resp.json()
        print(f"Ключи верхнего уровня: {list(data.keys())}")
        if 'temperature' in data:
            print(f"Температура: {data['temperature']}")
        else:
            print("Нет температуры")
        temp = data['temperature']['C']
        hum = data['humidity']['percent']
        return temp, hum
    except Exception as e:
        print(f"Ошибка для {city_name}: {e}")
        return None, None

def update_metrics():
    """Обновить все метрики"""
    for city, city_id in CITY_IDS.items():
        t, h = fetch_weather(city, city_id)
        if t is not None:
            temperature_gauge.labels(city=city).set(t)
            humidity_gauge.labels(city=city).set(h)
            print(f"{city}: {t}°C, влажность {h}%")
        else:
            # При ошибке можно пропустить или оставить старое значение
            pass
        time.sleep(1)  # вежливая пауза между запросами к серверу

if __name__ == "__main__":
    print("Запуск Weather Exporter с данными Gismeteo (v2, без токена)")
    start_http_server(8000)
    while True:
        update_metrics()
        print("--- Цикл обновления завершён. Следующий через 10 минут ---")
        time.sleep(600)  # обновление раз в 10 минут