#!/usr/bin/env python3
import time
import requests
import os
from prometheus_client import start_http_server, Gauge

# --- НАСТРОЙКИ ---
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

# --- Координаты городов (НОВЫЙ СЛОВАРЬ) ---
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

# --- Метрики Prometheus (ДОБАВЛЕНЫ лейблы lat, lon) ---
temperature_gauge = Gauge('weather_temp_celsius', 'Температура воздуха', ['city', 'lat', 'lon'])
humidity_gauge    = Gauge('weather_humidity_percent', 'Относительная влажность', ['city', 'lat', 'lon'])
pressure_gauge    = Gauge('weather_pressure_mmhg', 'Атмосферное давление (мм рт. ст.)', ['city', 'lat', 'lon'])
wind_speed_gauge  = Gauge('weather_wind_speed_ms', 'Скорость ветра (м/с)', ['city', 'lat', 'lon'])
feels_like_gauge  = Gauge('weather_feels_like_celsius', 'Ощущаемая температура', ['city', 'lat', 'lon'])
cloudiness_gauge  = Gauge('weather_cloudiness_percent', 'Облачность (%)', ['city', 'lat', 'lon'])

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
    """Обновляет метрики для всех городов."""
    for city_name, city_query in CITY_IDS.items():
        t, h, p, w, f, c = fetch_weather(city_name, city_query)

        # Получаем координаты города
        coords = CITY_COORDS.get(city_name, {"lat": 0, "lon": 0})
        lat = str(coords["lat"])
        lon = str(coords["lon"])

        if t is not None:
            t_rounded = round(t)                # температура до целого
            h_rounded = round(h) if h is not None else None  # влажность до целого
            p_rounded = round(p) if p is not None else None  # давление до целого
            w_rounded = round(w) if w is not None else None  # скорость ветра до целого
            f_rounded = round(f) if f is not None else None    # ощущаемая температура до целого
            c_rounded = round(c) if c is not None else None    # облачность до целого

            temperature_gauge.labels(city=city_name, lat=lat, lon=lon).set(t_rounded)
            if h_rounded is not None:
                humidity_gauge.labels(city=city_name, lat=lat, lon=lon).set(h_rounded)
            if p_rounded is not None:
                pressure_gauge.labels(city=city_name, lat=lat, lon=lon).set(p_rounded)
            if w_rounded is not None:
                wind_speed_gauge.labels(city=city_name, lat=lat, lon=lon).set(w_rounded)
            if f_rounded is not None:
                feels_like_gauge.labels(city=city_name, lat=lat, lon=lon).set(f_rounded)
            if c_rounded is not None:
                cloudiness_gauge.labels(city=city_name, lat=lat, lon=lon).set(c_rounded)

            print(f"{city_name}: {t_rounded}°C, влажность {h_rounded}%, "
                  f"давление {p_rounded} мм рт.ст., ветер {w_rounded} м/с, "
                  f"ощущается {f_rounded}°C, облачность {c_rounded}%")
        else:
            print(f"Не удалось получить данные для {city_name}")
        time.sleep(1)

if __name__ == "__main__":
    print("Запуск Weather Exporter (Gismeteo API v4 с токеном)")
    print(f"Лимит: 1000 запросов/месяц → интервал 36 часов")
    start_http_server(8000)
    while True:
        update_metrics()
        print("--- Цикл обновления завершён. Следующий через 36 часов ---")
        time.sleep(129600)  # 36 часов = 129600 секунд
