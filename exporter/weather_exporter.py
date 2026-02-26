#!/usr/bin/env python3
import time
import requests
import os
from prometheus_client import start_http_server, Gauge, Counter

# --- НАСТРОЙКИ ---
GISMETEO_TOKEN = os.getenv('GISMETEO_TOKEN')
if not GISMETEO_TOKEN:
    raise ValueError("Переменная окружения GISMETEO_TOKEN не установлена!")
BASE_URL = "https://api.gismeteo.net/v4/weather/current"

# --- Метрики Prometheus с координатами ---
temperature_gauge = Gauge('weather_temp_celsius', 'Температура воздуха', ['city', 'lat', 'lon'])
humidity_gauge    = Gauge('weather_humidity_percent', 'Относительная влажность', ['city', 'lat', 'lon'])
pressure_gauge    = Gauge('weather_pressure_mmhg', 'Атмосферное давление (мм рт. ст.)', ['city', 'lat', 'lon'])
wind_speed_gauge  = Gauge('weather_wind_speed_ms', 'Скорость ветра (м/с)', ['city', 'lat', 'lon'])
feels_like_gauge  = Gauge('weather_feels_like_celsius', 'Ощущаемая температура', ['city', 'lat', 'lon'])
cloudiness_gauge  = Gauge('weather_cloudiness_percent', 'Облачность (%)', ['city', 'lat', 'lon'])

# --- Метрики для мониторинга работы самого экспортера ---
errors_counter = Counter('weather_api_errors_total', 'Количество ошибок API', ['city'])
success_counter = Counter('weather_api_success_total', 'Количество успешных запросов', ['city'])

# --- Словарь городов и координат (ваш существующий список) ---
CITY_IDS = { ... }  # ваш словарь с названиями и поисковыми запросами
CITY_COORDS = { ... }  # ваш словарь с координатами

def fetch_weather_with_retry(city_name, city_query, retries=3, timeout=15):
    """Запрос к API с повторными попытками при ошибках"""
    headers = {
        "X-Gismeteo-Token": GISMETEO_TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    params = {
        "name": city_query,
        "locale": "ru-RU"
    }

    for attempt in range(retries):
        try:
            resp = requests.get(BASE_URL, headers=headers, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            current = data.get('current', {})
            if not current:
                print(f"Предупреждение: нет данных 'current' для {city_name}")
                # При отсутствии данных возвращаем None, но не считаем это фатальной ошибкой
                return None, None, None, None, None, None

            temp = current.get('temperature_air')
            hum = current.get('humidity')
            pressure = current.get('pressure')
            wind_speed = current.get('wind_speed')
            feels_like = current.get('temperature_heat_index')
            cloudiness = current.get('cloudiness')

            # Успешный запрос
            success_counter.labels(city=city_name).inc()
            return temp, hum, pressure, wind_speed, feels_like, cloudiness

        except requests.exceptions.Timeout:
            print(f"Таймаут для {city_name}, попытка {attempt+1}/{retries}")
            if attempt == retries - 1:
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None
            time.sleep(2)  # пауза перед повтором

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                print(f"Ошибка 429 (лимит) для {city_name}. Увеличьте интервал.")
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None
            elif resp.status_code == 401:
                print(f"Ошибка 401: Неверный токен для {city_name}. Проверьте GISMETEO_TOKEN.")
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None
            else:
                print(f"HTTP ошибка {resp.status_code} для {city_name}: {e}")
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None

        except Exception as e:
            print(f"Неизвестная ошибка для {city_name}: {e}")
            errors_counter.labels(city=city_name).inc()
            return None, None, None, None, None, None

    return None, None, None, None, None, None

def update_metrics():
    """Обновляет метрики для всех городов с сохранением старых значений при ошибках"""
    print(f"\n--- Начало цикла обновления: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    success_count = 0
    error_count = 0

    for city_name, city_query in CITY_IDS.items():
        t, h, p, w, f, c = fetch_weather_with_retry(city_name, city_query)
        coords = CITY_COORDS.get(city_name, {"lat": 0, "lon": 0})
        lat = str(coords["lat"])
        lon = str(coords["lon"])

        if t is not None:
            # Округление значений
            t_rounded = round(t)
            h_rounded = round(h) if h is not None else None
            p_rounded = round(p) if p is not None else None
            w_rounded = round(w, 1) if w is not None else None
            f_rounded = round(f) if f is not None else None
            c_rounded = round(c) if c is not None else None

            # Обновляем метрики
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

            print(f"✅ {city_name}: {t_rounded}°C, влажность {h_rounded}%")
            success_count += 1
        else:
            # При ошибке НЕ удаляем старую метрику - она остаётся в Prometheus
            print(f"⚠️ {city_name}: данные не получены (сохранены предыдущие значения)")
            error_count += 1

        # Небольшая пауза между запросами, чтобы не нагружать API
        time.sleep(0.5)

    print(f"--- Цикл завершён. Успешно: {success_count}, ошибок: {error_count} ---")

if __name__ == "__main__":
    print("Запуск Weather Exporter (стабильная версия с сохранением метрик)")
    print(f"Всего городов: {len(CITY_IDS)}")
    start_http_server(8000)
    while True:
        update_metrics()
        print(f"--- Следующий цикл через 5 дней ---")
        time.sleep(432000)  # 5 дней