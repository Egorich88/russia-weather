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

# --- Словарь городов: название -> поисковый запрос (90 городов) ---
CITY_IDS = {
    # Центральный федеральный округ (17 городов)
    "Москва": "москва",
    "Белгород": "белгород",
    "Брянск": "брянск",
    "Владимир": "владимир",
    "Воронеж": "воронеж",
    "Иваново": "иваново",
    "Калуга": "калуга",
    "Кострома": "кострома",
    "Курск": "курск",
    "Липецк": "липецк",
    "Орел": "орел",
    "Рязань": "рязань",
    "Смоленск": "смоленск",
    "Тамбов": "тамбов",
    "Тверь": "тверь",
    "Тула": "тула",
    "Ярославль": "ярославль",

    # Северо-Западный федеральный округ (8 городов)
    "Санкт-Петербург": "санкт-петербург",
    "Петрозаводск": "петрозаводск",
    "Сыктывкар": "сыктывкар",
    "Архангельск": "архангельск",
    "Вологда": "вологда",
    "Калининград": "калининград",
    "Мурманск": "мурманск",
    "Великий Новгород": "великий новгород",
    "Псков": "псков",

    # Южный федеральный округ (10 городов)
    "Астрахань": "астрахань",
    "Волгоград": "волгоград",
    "Ростов-на-Дону": "ростов-на-дону",
    "Краснодар": "краснодар",
    "Севастополь": "севастополь",
    "Симферополь": "симферополь",
    "Сочи": "сочи",
    "Новороссийск": "новороссийск",
    "Майкоп": "майкоп",
    "Элиста": "элиста",

    # Северо-Кавказский федеральный округ (7 городов)
    "Махачкала": "махачкала",
    "Назрань": "назрань",
    "Нальчик": "нальчик",
    "Владикавказ": "владикавказ",
    "Черкесск": "черкесск",
    "Грозный": "грозный",
    "Ставрополь": "ставрополь",

    # Приволжский федеральный округ (14 городов)
    "Уфа": "уфа",
    "Йошкар-Ола": "йошкар-ола",
    "Саранск": "саранск",
    "Казань": "казань",
    "Ижевск": "ижевск",
    "Чебоксары": "чебоксары",
    "Киров": "киров",
    "Нижний Новгород": "нижний новгород",
    "Оренбург": "оренбург",
    "Пенза": "пенза",
    "Пермь": "пермь",
    "Самара": "самара",
    "Саратов": "саратов",
    "Ульяновск": "ульяновск",
    "Тольятти": "тольятти",
    "Набережные Челны": "набережные челны",

    # Уральский федеральный округ (8 городов)
    "Курган": "курган",
    "Екатеринбург": "екатеринбург",
    "Тюмень": "тюмень",
    "Челябинск": "челябинск",
    "Магнитогорск": "магнитогорск",
    "Нижний Тагил": "нижний тагил",
    "Ханты-Мансийск": "ханты-мансийск",
    "Салехард": "салехард",

    # Сибирский федеральный округ (11 городов)
    "Горно-Алтайск": "горно-алтайск",
    "Барнаул": "барнаул",
    "Новокузнецк": "новокузнецк",
    "Кемерово": "кемерово",
    "Абакан": "абакан",
    "Красноярск": "красноярск",
    "Новосибирск": "новосибирск",
    "Омск": "омск",
    "Томск": "томск",
    "Иркутск": "иркутск",
    "Улан-Удэ": "улан-удэ",
    "Чита": "чита",

    # Дальневосточный федеральный округ (11 городов)
    "Благовещенск": "благовещенск",
    "Биробиджан": "биробиджан",
    "Петропавловск-Камчатский": "петропавловск-камчатский",
    "Магадан": "магадан",
    "Владивосток": "владивосток",
    "Хабаровск": "хабаровск",
    "Южно-Сахалинск": "южно-сахалинск",
    "Анадырь": "анадырь",
    "Якутск": "якутск",
    "Комсомольск-на-Амуре": "комсомольск-на-амуре",
    "Тында": "тында",
}

# --- Координаты городов (для карты) ---
CITY_COORDS = {
    "Москва": {"lat": 55.7558, "lon": 37.6176},
    "Белгород": {"lat": 50.5977, "lon": 36.5858},
    "Брянск": {"lat": 53.2434, "lon": 34.3644},
    "Владимир": {"lat": 56.1366, "lon": 40.3966},
    "Воронеж": {"lat": 51.6755, "lon": 39.2089},
    "Иваново": {"lat": 57.0003, "lon": 40.9739},
    "Калуга": {"lat": 54.5293, "lon": 36.2754},
    "Кострома": {"lat": 57.7671, "lon": 40.9269},
    "Курск": {"lat": 51.7304, "lon": 36.1926},
    "Липецк": {"lat": 52.6103, "lon": 39.5942},
    "Орел": {"lat": 52.9674, "lon": 36.0804},
    "Рязань": {"lat": 54.6294, "lon": 39.7416},
    "Смоленск": {"lat": 54.7887, "lon": 32.0402},
    "Тамбов": {"lat": 52.7317, "lon": 41.4439},
    "Тверь": {"lat": 56.8584, "lon": 35.9116},
    "Тула": {"lat": 54.1931, "lon": 37.6174},
    "Ярославль": {"lat": 57.6221, "lon": 39.8915},
    "Санкт-Петербург": {"lat": 59.9343, "lon": 30.3351},
    "Петрозаводск": {"lat": 61.7891, "lon": 34.3597},
    "Сыктывкар": {"lat": 61.6687, "lon": 50.8099},
    "Архангельск": {"lat": 64.5393, "lon": 40.5169},
    "Вологда": {"lat": 59.2205, "lon": 39.8915},
    "Калининград": {"lat": 54.7065, "lon": 20.5111},
    "Мурманск": {"lat": 68.9696, "lon": 33.0745},
    "Великий Новгород": {"lat": 58.5213, "lon": 31.2719},
    "Псков": {"lat": 57.8207, "lon": 28.3348},
    "Астрахань": {"lat": 46.3497, "lon": 48.0408},
    "Волгоград": {"lat": 48.7071, "lon": 44.5169},
    "Ростов-на-Дону": {"lat": 47.2357, "lon": 39.7015},
    "Краснодар": {"lat": 45.0448, "lon": 38.9760},
    "Севастополь": {"lat": 44.6167, "lon": 33.5254},
    "Симферополь": {"lat": 44.9521, "lon": 34.1024},
    "Сочи": {"lat": 43.6028, "lon": 39.7342},
    "Новороссийск": {"lat": 44.7151, "lon": 37.7689},
    "Майкоп": {"lat": 44.6050, "lon": 40.1040},
    "Элиста": {"lat": 46.3083, "lon": 44.2701},
    "Махачкала": {"lat": 42.9849, "lon": 47.5046},
    "Назрань": {"lat": 43.2259, "lon": 44.7642},
    "Нальчик": {"lat": 43.4853, "lon": 43.6070},
    "Владикавказ": {"lat": 43.0205, "lon": 44.6819},
    "Черкесск": {"lat": 44.2233, "lon": 42.0577},
    "Грозный": {"lat": 43.3179, "lon": 45.6981},
    "Ставрополь": {"lat": 45.0428, "lon": 41.9734},
    "Уфа": {"lat": 54.7388, "lon": 55.9721},
    "Йошкар-Ола": {"lat": 56.6341, "lon": 47.8999},
    "Саранск": {"lat": 54.1868, "lon": 45.1838},
    "Казань": {"lat": 55.7887, "lon": 49.1221},
    "Ижевск": {"lat": 56.8528, "lon": 53.2115},
    "Чебоксары": {"lat": 56.1439, "lon": 47.2489},
    "Киров": {"lat": 58.6035, "lon": 49.6680},
    "Нижний Новгород": {"lat": 56.2965, "lon": 43.9361},
    "Оренбург": {"lat": 51.7727, "lon": 55.0988},
    "Пенза": {"lat": 53.1950, "lon": 45.0183},
    "Пермь": {"lat": 58.0105, "lon": 56.2502},
    "Самара": {"lat": 53.2415, "lon": 50.2212},
    "Саратов": {"lat": 51.5336, "lon": 46.0342},
    "Ульяновск": {"lat": 54.3282, "lon": 48.3866},
    "Тольятти": {"lat": 53.5113, "lon": 49.4185},
    "Набережные Челны": {"lat": 55.7436, "lon": 52.3958},
    "Курган": {"lat": 55.4472, "lon": 65.3414},
    "Екатеринбург": {"lat": 56.8389, "lon": 60.6057},
    "Тюмень": {"lat": 57.1522, "lon": 65.5272},
    "Челябинск": {"lat": 55.1644, "lon": 61.4368},
    "Магнитогорск": {"lat": 53.4186, "lon": 58.9827},
    "Нижний Тагил": {"lat": 57.9102, "lon": 59.9708},
    "Ханты-Мансийск": {"lat": 61.0024, "lon": 69.0016},
    "Салехард": {"lat": 66.5374, "lon": 66.6015},
    "Горно-Алтайск": {"lat": 51.9582, "lon": 85.9609},
    "Барнаул": {"lat": 53.3542, "lon": 83.7697},
    "Новокузнецк": {"lat": 53.7550, "lon": 87.1098},
    "Кемерово": {"lat": 55.3551, "lon": 86.0872},
    "Абакан": {"lat": 53.7209, "lon": 91.4402},
    "Красноярск": {"lat": 56.0153, "lon": 92.8932},
    "Новосибирск": {"lat": 55.0084, "lon": 82.9357},
    "Омск": {"lat": 54.9893, "lon": 73.3682},
    "Томск": {"lat": 56.4959, "lon": 84.9722},
    "Иркутск": {"lat": 52.2896, "lon": 104.2806},
    "Улан-Удэ": {"lat": 51.8335, "lon": 107.5841},
    "Чита": {"lat": 52.0331, "lon": 113.4995},
    "Благовещенск": {"lat": 50.2907, "lon": 127.5272},
    "Биробиджан": {"lat": 48.7911, "lon": 132.9380},
    "Петропавловск-Камчатский": {"lat": 53.0370, "lon": 158.6559},
    "Магадан": {"lat": 59.5684, "lon": 150.8085},
    "Владивосток": {"lat": 43.1332, "lon": 131.9113},
    "Хабаровск": {"lat": 48.4802, "lon": 135.0719},
    "Южно-Сахалинск": {"lat": 46.9642, "lon": 142.7364},
    "Анадырь": {"lat": 64.7341, "lon": 177.5144},
    "Якутск": {"lat": 62.0278, "lon": 129.7320},
    "Комсомольск-на-Амуре": {"lat": 50.5499, "lon": 137.0079},
    "Тында": {"lat": 55.1500, "lon": 124.7167},
}

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
                return None, None, None, None, None, None

            temp = current.get('temperature_air')
            hum = current.get('humidity')
            pressure = current.get('pressure')
            wind_speed = current.get('wind_speed')
            feels_like = current.get('temperature_heat_index')
            cloudiness = current.get('cloudiness')

            success_counter.labels(city=city_name).inc()
            return temp, hum, pressure, wind_speed, feels_like, cloudiness

        except requests.exceptions.Timeout:
            print(f"Таймаут для {city_name}, попытка {attempt+1}/{retries}")
            if attempt == retries - 1:
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None
            time.sleep(2)

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                print(f"Ошибка 429 (лимит) для {city_name}")
                errors_counter.labels(city=city_name).inc()
                return None, None, None, None, None, None
            elif resp.status_code == 401:
                print(f"Ошибка 401: Неверный токен для {city_name}")
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
            t_rounded = round(t)
            h_rounded = round(h) if h is not None else None
            p_rounded = round(p) if p is not None else None
            w_rounded = round(w) if w is not None else None
            f_rounded = round(f) if f is not None else None
            c_rounded = round(c) if c is not None else None

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
            print(f"⚠️ {city_name}: данные не получены (сохранены предыдущие значения)")
            error_count += 1

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