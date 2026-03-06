#!/usr/bin/env python3
import time
import requests
import os
from datetime import datetime, timedelta, timezone
from prometheus_client import start_http_server, Gauge, Info, Counter

# --- НАСТРОЙКИ ---
GISMETEO_TOKEN = os.getenv('GISMETEO_TOKEN')
if not GISMETEO_TOKEN:
    raise ValueError("Переменная окружения GISMETEO_TOKEN не установлена!")
BASE_URL = "https://api.gismeteo.net/v4/weather/current"

# --- Словарь соответствия кодов иконок ---
ICON_MAPPING = {
    'd': 'd_c0',      # базовый день → ясно
    'n': 'n_c0',      # базовая ночь → ясно ночью
    # все остальные коды совпадают с названиями файлов
}

# --- Словарь городов: название -> поисковый запрос (90 городов) ---
CITY_IDS = {
    # (ваш полный список городов, он уже есть, оставляем как есть)
    "Москва": "москва",
    # ... остальные
}

# --- Координаты городов ---
CITY_COORDS = {
    # (ваш полный словарь координат, оставляем как есть)
}

# --- Метрики Prometheus (числовые) ---
temperature_gauge = Gauge('weather_temp_celsius', 'Температура воздуха', ['city', 'lat', 'lon'])
humidity_gauge    = Gauge('weather_humidity_percent', 'Относительная влажность', ['city', 'lat', 'lon'])
pressure_gauge    = Gauge('weather_pressure_mmhg', 'Атмосферное давление (мм рт. ст.)', ['city', 'lat', 'lon'])
wind_speed_gauge  = Gauge('weather_wind_speed_ms', 'Скорость ветра (м/с)', ['city', 'lat', 'lon'])
feels_like_gauge  = Gauge('weather_feels_like_celsius', 'Ощущаемая температура', ['city', 'lat', 'lon'])

# --- Метрики для текстовой информации ---
weather_icon_info = Info('weather_icon', 'Код иконки погоды', ['city'])
weather_description_info = Info('weather_description', 'Описание погоды', ['city'])

# --- НОВАЯ МЕТРИКА: строковое время ---
time_str_info = Info('weather_time_str', 'Местное время в формате ЧЧ:ММ', ['city'])

# --- Счётчики ошибок ---
errors_counter = Counter('weather_api_errors_total', 'Количество ошибок API', ['city'])
success_counter = Counter('weather_api_success_total', 'Количество успешных запросов', ['city'])

# --- МЕТРИКА: Часовой пояс (смещение в минутах) ---
timezone_offset_gauge = Gauge('weather_timezone_offset_minutes', 'Смещение часового пояса от UTC (в минутах)', ['city'])

# --- МЕТРИКА: Местное время (timestamp) ---
local_time_gauge = Gauge('weather_local_time', 'Местное время города (timestamp)', ['city'])

def fetch_weather_with_retry(city_name, city_query, retries=3, timeout=15):
    """Запрос к API с повторными попытками при ошибках, включая часовой пояс"""
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

                # Получаем location для часового пояса
                location = data.get('location', {})
                offset = location.get('time_zone_offset', 0)  # в минутах

                current = data.get('current', {})
                if not current:
                    print(f"Предупреждение: нет данных 'current' для {city_name}")
                    return None, None, None, None, None, None, None, None, None

                temp = current.get('temperature_air')
                hum = current.get('humidity')
                pressure = current.get('pressure')
                wind_speed = current.get('wind_speed')
                feels_like = current.get('temperature_heat_index')
                icon = current.get('icon_weather')
                description = current.get('description')

                success_counter.labels(city=city_name).inc()
                return temp, hum, pressure, wind_speed, feels_like, icon, description, offset

            except requests.exceptions.Timeout:
                print(f"Таймаут для {city_name}, попытка {attempt+1}/{retries}")
                if attempt == retries - 1:
                    errors_counter.labels(city=city_name).inc()
                    return None, None, None, None, None, None, None, None, None
                time.sleep(2)

            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:
                    print(f"Ошибка 429 (лимит) для {city_name}")
                    errors_counter.labels(city=city_name).inc()
                    return None, None, None, None, None, None, None, None, None
                elif resp.status_code == 401:
                    print(f"Ошибка 401: Неверный токен для {city_name}")
                    errors_counter.labels(city=city_name).inc()
                    return None, None, None, None, None, None, None, None, None
                else:
                    print(f"HTTP ошибка {resp.status_code} для {city_name}: {e}")
                    errors_counter.labels(city=city_name).inc()
                    return None, None, None, None, None, None, None, None, None

            except Exception as e:
                print(f"Неизвестная ошибка для {city_name}: {e}")
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None, None, None, None

        return None, None, None, None, None, None, None, None, None

def update_metrics():
    print(f"\n--- Начало цикла обновления: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    success_count = 0
    error_count = 0

    for city_name, city_query in CITY_IDS.items():
        t, h, p, w, f, icon, desc, offset = fetch_weather_with_retry(city_name, city_query)
        coords = CITY_COORDS.get(city_name, {"lat": 0, "lon": 0})
        lat = str(coords["lat"])
        lon = str(coords["lon"])

        if t is not None:
            # ... округление и обновление числовых метрик ...

            # --- ОБРАБОТКА ИКОНОК ---
            if icon is not None:
                mapped_icon = ICON_MAPPING.get(icon, icon)
                icon_url = f"/public/img/icons/gismeteo/{mapped_icon}.png"
                icon_html = f"<img src='{icon_url}' style='width:30px; height:30px;'>"
                weather_icon_info.labels(city=city_name).info({
                    'code': mapped_icon,
                    'original_code': icon,
                    'url': icon_url,
                    'html': icon_html
                })

            if desc is not None:
                weather_description_info.labels(city=city_name).info({'text': desc})

            if offset is not None:
                timezone_offset_gauge.labels(city=city_name).set(offset)

                # --- РАСЧЁТ МЕСТНОГО ВРЕМЕНИ ---
                now_utc = datetime.now(timezone.utc)
                city_datetime = now_utc + timedelta(minutes=offset)
                city_timestamp = int(city_datetime.timestamp())
                local_time_gauge.labels(city=city_name).set(city_timestamp)

                # --- НОВАЯ СТРОКОВАЯ МЕТРИКА ---
                time_str = city_datetime.strftime('%H:%M')
                time_str_info.labels(city=city_name).info({'time': time_str})

                print(f"   ⏰ {city_name}: UTC={now_utc.strftime('%H:%M')} +{offset}мин = {time_str}")

            print(f"✅ {city_name}: {t_rounded}°C, ветер {w_rounded} м/с, иконка {icon} → {mapped_icon if icon else 'None'}, описание: {desc}, часовой пояс: {offset} мин")
            success_count += 1
        else:
            print(f"⚠️ {city_name}: данные не получены (сохранены предыдущие значения)")
            error_count += 1

        time.sleep(0.5)

    print(f"--- Цикл завершён. Успешно: {success_count}, ошибок: {error_count} ---")

if __name__ == "__main__":
    print("Запуск Weather Exporter (версия с часовыми поясами, иконками и маппингом)")
    print(f"Всего городов: {len(CITY_IDS)}")
    start_http_server(8000)
    while True:
        update_metrics()
        print(f"--- Следующий цикл через 5 дней ---")
        time.sleep(432000)  # 5 дней