#!/usr/bin/env python3
import time
import requests
import os
from prometheus_client import start_http_server, Gauge

# --- НАСТРОЙКИ (обязательно замените TOKEN) ---
GISMETEO_TOKEN = os.getenv('GISMETEO_TOKEN')
if not GISMETEO_TOKEN:
    raise ValueError("Переменная окружения GISMETEO_TOKEN не установлена!")
BASE_URL = "https://api.gismeteo.net/v4/weather/current"

# --- Словарь городов (без изменений) ---
CITY_IDS = {
    "Москва": "москва",
    "Санкт-Петербург": "санкт-петербург",
    "Новосибирск": "новосибирск",
    "Екатеринбург": "екатеринбург",
    "Казань": "казань",
    "Нижний Новгород": "нижний новгород",
    "Челябинск": "челябинск",
    "Омск": "омск",
    "Самара": "самара",
    "Ростов-на-Дону": "ростов-на-дону",
    "Уфа": "уфа",
    "Красноярск": "красноярск",
    "Пермь": "пермь",
    "Воронеж": "воронеж",
    "Волгоград": "волгоград",
    "Краснодар": "краснодар",
    "Саратов": "саратов",
    "Тюмень": "тюмень",
    "Тольятти": "тольятти",
    "Ижевск": "ижевск",
    "Барнаул": "барнаул",
    "Ульяновск": "ульяновск",
    "Иркутск": "иркутск",
    "Хабаровск": "хабаровск",
    "Ярославль": "ярославль",
    "Владивосток": "владивосток",
    "Махачкала": "махачкала",
    "Томск": "томск",
    "Оренбург": "оренбург",
    "Кемерово": "кемерово",
    "Новокузнецк": "новокузнецк",
    "Рязань": "рязань",
    "Астрахань": "астрахань",
    "Набережные Челны": "набережные челны",
    "Пенза": "пенза",
    "Липецк": "липецк",
    "Киров": "киров",
    "Чебоксары": "чебоксары",
    "Тула": "тула",
    "Калининград": "калининград",
    "Курск": "курск",
    "Севастополь": "севастополь",
    "Сочи": "сочи",
    "Симферополь": "симферополь",
    "Мурманск": "мурманск",
    "Архангельск": "архангельск",
    "Якутск": "якутск",
    "Петропавловск-Камчатский": "петропавловск-камчатский",
    "Магадан": "магадан",
    "Анадырь": "анадырь",
    "Южно-Сахалинск": "южно-сахалинск",
    "Комсомольск-на-Амуре": "комсомольск-на-амуре",
    "Благовещенск": "благовещенск",
    "Тында": "тында",
}

# --- Метрики Prometheus (без изменений) ---
temperature_gauge = Gauge('weather_temp_celsius', 'Температура воздуха', ['city'])
humidity_gauge    = Gauge('weather_humidity_percent', 'Относительная влажность', ['city'])
pressure_gauge    = Gauge('weather_pressure_mmhg', 'Атмосферное давление (мм рт. ст.)', ['city'])
wind_speed_gauge  = Gauge('weather_wind_speed_ms', 'Скорость ветра (м/с)', ['city'])
feels_like_gauge  = Gauge('weather_feels_like_celsius', 'Ощущаемая температура', ['city'])
cloudiness_gauge  = Gauge('weather_cloudiness_percent', 'Облачность (%)', ['city'])

def fetch_weather(city_name, city_query):
    """Получает данные через официальное API Gismeteo v4 с токеном."""
    headers = {
        "X-Gismeteo-Token": GISMETEO_TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    params = {
        "name": city_query,
        "locale": "ru-RU"
    }

    try:
        resp = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Данные текущей погоды находятся в объекте 'current'
        current = data.get('current', {})
        if not current:
            print(f"Нет данных current для {city_name}")
            return None, None, None, None, None, None

        # Извлекаем все нужные поля
        temp = current.get('temperature_air')
        hum = current.get('humidity')
        pressure = current.get('pressure')
        wind_speed = current.get('wind_speed')
        feels_like = current.get('temperature_heat_index')  # Ощущаемая температура
        cloudiness = current.get('cloudiness')

        return temp, hum, pressure, wind_speed, feels_like, cloudiness

    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            print(f"Ошибка 401: Неверный токен для {city_name}. Проверьте GISMETEO_TOKEN.")
        elif resp.status_code == 429:
            print(f"Ошибка 429: Превышен лимит запросов для {city_name}. Увеличьте интервал.")
        else:
            print(f"HTTP ошибка для {city_name} (запрос '{city_query}'): {e}")
    except Exception as e:
        print(f"Неизвестная ошибка для {city_name} (запрос '{city_query}'): {e}")

    return None, None, None, None, None, None

def update_metrics():
    """Обновляет метрики для всех городов (вызывается раз в час)."""
    for city_name, city_query in CITY_IDS.items():
        t, h, p, w, f, c = fetch_weather(city_name, city_query)
        if t is not None:
            temperature_gauge.labels(city=city_name).set(t)
            if h is not None:
                humidity_gauge.labels(city=city_name).set(h)
            if p is not None:
                pressure_gauge.labels(city=city_name).set(p)
            if w is not None:
                wind_speed_gauge.labels(city=city_name).set(w)
            if f is not None:
                feels_like_gauge.labels(city=city_name).set(f)
            if c is not None:
                cloudiness_gauge.labels(city=city_name).set(c)
            print(f"{city_name}: {t}°C, влажность {h}%, давление {p} мм рт.ст., "
                  f"ветер {w} м/с, ощущается {f}°C, облачность {c}%")
        else:
            print(f"Не удалось получить данные для {city_name}")
        time.sleep(1)  # Небольшая пауза между запросами к API

if __name__ == "__main__":
    print("Запуск Weather Exporter (Gismeteo API v4 с токеном)")
    print(f"Лимит: ~720 запросов/месяц при интервале 1 час")
    start_http_server(8000)
    while True:
        update_metrics()
        print("--- Цикл обновления завершён. Следующий через 1 час ---")
        time.sleep(3600)  # 1 час = 3600 секунд