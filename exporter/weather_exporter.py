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
# Координаты (добавить после CITY_IDS)
CITY_COORDS = {
    "Москва": {"lat": 55.7558, "lon": 37.6176},
    "Санкт-Петербург": {"lat": 59.9343, "lon": 30.3351},
    "Новосибирск": {"lat": 55.0084, "lon": 82.9357},
    "Екатеринбург": {"lat": 56.8389, "lon": 60.6057},
    "Казань": {"lat": 55.7887, "lon": 49.1221},
    "Нижний Новгород": {"lat": 56.2965, "lon": 43.9361},
    "Челябинск": {"lat": 55.1644, "lon": 61.4368},
    "Омск": {"lat": 54.9893, "lon": 73.3682},
    "Самара": {"lat": 53.2415, "lon": 50.2212},
    "Ростов-на-Дону": {"lat": 47.2357, "lon": 39.7015},
    "Уфа": {"lat": 54.7388, "lon": 55.9721},
    "Красноярск": {"lat": 56.0153, "lon": 92.8932},
    "Пермь": {"lat": 58.0105, "lon": 56.2502},
    "Воронеж": {"lat": 51.6755, "lon": 39.2089},
    "Волгоград": {"lat": 48.7071, "lon": 44.5169},
    "Краснодар": {"lat": 45.0448, "lon": 38.9760},
    "Саратов": {"lat": 51.5336, "lon": 46.0342},
    "Тюмень": {"lat": 57.1522, "lon": 65.5272},
    "Тольятти": {"lat": 53.5113, "lon": 49.4185},
    "Ижевск": {"lat": 56.8528, "lon": 53.2115},
    "Барнаул": {"lat": 53.3542, "lon": 83.7697},
    "Ульяновск": {"lat": 54.3282, "lon": 48.3866},
    "Иркутск": {"lat": 52.2896, "lon": 104.2806},
    "Хабаровск": {"lat": 48.4802, "lon": 135.0719},
    "Ярославль": {"lat": 57.6221, "lon": 39.8915},
    "Владивосток": {"lat": 43.1332, "lon": 131.9113},
    "Махачкала": {"lat": 42.9849, "lon": 47.5046},
    "Томск": {"lat": 56.4959, "lon": 84.9722},
    "Оренбург": {"lat": 51.7727, "lon": 55.0988},
    "Кемерово": {"lat": 55.3551, "lon": 86.0872},
    "Новокузнецк": {"lat": 53.7550, "lon": 87.1098},
    "Рязань": {"lat": 54.6294, "lon": 39.7416},
    "Астрахань": {"lat": 46.3497, "lon": 48.0408},
    "Набережные Челны": {"lat": 55.7436, "lon": 52.3958},
    "Пенза": {"lat": 53.1950, "lon": 45.0183},
    "Липецк": {"lat": 52.6103, "lon": 39.5942},
    "Киров": {"lat": 58.6035, "lon": 49.6680},
    "Чебоксары": {"lat": 56.1439, "lon": 47.2489},
    "Тула": {"lat": 54.1931, "lon": 37.6174},
    "Калининград": {"lat": 54.7065, "lon": 20.5111},
    "Курск": {"lat": 51.7304, "lon": 36.1926},
    "Севастополь": {"lat": 44.6167, "lon": 33.5254},
    "Сочи": {"lat": 43.6028, "lon": 39.7342},
    "Симферополь": {"lat": 44.9521, "lon": 34.1024},
    "Мурманск": {"lat": 68.9696, "lon": 33.0745},
    "Архангельск": {"lat": 64.5393, "lon": 40.5169},
    "Якутск": {"lat": 62.0278, "lon": 129.7320},
    "Петропавловск-Камчатский": {"lat": 53.0370, "lon": 158.6559},
    "Магадан": {"lat": 59.5684, "lon": 150.8085},
    "Анадырь": {"lat": 64.7341, "lon": 177.5144},
    "Южно-Сахалинск": {"lat": 46.9642, "lon": 142.7364},
    "Комсомольск-на-Амуре": {"lat": 50.5499, "lon": 137.0079},
    "Благовещенск": {"lat": 50.2907, "lon": 127.5272},
    "Тында": {"lat": 55.1500, "lon": 124.7167},
}

# Публичный эндпоинт Gismeteo (без токена)
BASE_URL = "https://www.gismeteo.com/api/v2/weather/current/{}"

# --- Метрики Prometheus ---
# (существующие + новые)
temperature_gauge = Gauge('weather_temp_celsius', 'Температура воздуха', ['city', 'lat', 'lon'])
humidity_gauge    = Gauge('weather_humidity_percent', 'Относительная влажность', ['city', 'lat', 'lon'])
pressure_gauge    = Gauge('weather_pressure_mmhg', 'Атмосферное давление (мм рт. ст.)', ['city', 'lat', 'lon'])
wind_speed_gauge  = Gauge('weather_wind_speed_ms', 'Скорость ветра (м/с)', ['city', 'lat', 'lon'])
feels_like_gauge  = Gauge('weather_feels_like_celsius', 'Ощущаемая температура', ['city', 'lat', 'lon'])
cloudiness_gauge  = Gauge('weather_cloudiness_percent', 'Облачность (%)', ['city', 'lat', 'lon'])

def fetch_weather(city_name, city_id):
    url = BASE_URL.format(city_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.gismeteo.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Ответ для {city_name}: статус {resp.status_code}")
        data = resp.json()
        print(f"Ключи ответа: {list(data.keys())}")
        # принудительно покажем всю структуру
        print(f"Полный ответ: {data}")
        temp = data['temperature']['air']['C']
        hum = data['humidity']['percent']
        pressure = data.get('pressure', {}).get('mm_hg_atm')
        wind_speed = data.get('wind', {}).get('speed', {}).get('m_s')
        feels_like = data.get('temperature', {}).get('comfort', {}).get('C')
        cloudiness = data.get('cloudiness', {}).get('percent')
        return temp, hum, pressure, wind_speed, feels_like, cloudiness
    except Exception as e:
        print(f"Ошибка для {city_name} (ID {city_id}): {e}")
        return None, None, None, None, None, None

def update_metrics():
    """Обновить все метрики для всех городов"""
    for city, city_id in CITY_IDS.items():
        t, h, p, w, f, c = fetch_weather(city, city_id)
         coords = CITY_COORDS.get(city, {"lat": 0, "lon": 0})
        if t is not None:
            temperature_gauge.labels(city=city, lat=str(coords["lat"]), lon=str(coords["lon"])).set(t)
            if h is not None:
                humidity_gauge.labels(city=city, lat=str(coords["lat"]), lon=str(coords["lon"])).set(h)
            if p is not None:
                pressure_gauge.labels(city=city, lat=str(coords["lat"]), lon=str(coords["lon"])).setp)
            if w is not None:
                wind_speed_gauge.labels(city=city, lat=str(coords["lat"]), lon=str(coords["lon"])).set(w)
            if f is not None:
                feels_like_gauge.labels(city=city, lat=str(coords["lat"]), lon=str(coords["lon"])).set(f)
            if c is not None:
                cloudiness_gauge.labels(city=city, lat=str(coords["lat"]), lon=str(coords["lon"])).set(c)
            print(f"{city}: {t}°C, влажность {h}%, давление {p} мм рт.ст., ветер {w} м/с, ощущается {f}°C, облачность {c}%")
        else:
            print(f"Не удалось получить данные для {city}")
        time.sleep(1)  # вежливая пауза между городами

if __name__ == "__main__":
    print("Запуск Weather Exporter (расширенная версия)")
    start_http_server(8000)
    while True:
        update_metrics()
        print("--- Цикл обновления завершён. Следующий через 10 минут ---")
        time.sleep(600)