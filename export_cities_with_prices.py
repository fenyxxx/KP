# -*- coding: utf-8 -*-
import sqlite3
import csv

# Примерные цены на детские билеты в плацкарте от Нового Уренгоя (в рублях)
# Основано на веб-поиске и приблизительных расчетах
# Цены актуальны на октябрь 2024 года

# Базовые цены по направлениям и расстояниям
def estimate_price(city):
    """Оценка стоимости билета на основе направления и примерного расстояния"""
    
    city_lower = city.lower()
    
    # Точные данные из веб-поиска
    if 'москва' in city_lower or 'московск' in city_lower:
        return 3559  # Из веб-поиска
    elif 'екатеринбург' in city_lower:
        return 3035  # Из веб-поиска
    elif 'дружинин' in city_lower:
        return 2704  # Из веб-поиска
    
    # Ближние направления (Урал, Западная Сибирь) - 2500-3500 руб
    elif any(word in city_lower for word in ['тюмень', 'курган', 'омск', 'томск', 'усинск']):
        return 3000
    
    # Средние направления (Поволжье, Урал) - 3500-4500 руб
    elif any(word in city_lower for word in ['казань', 'самар', 'пермь', 'уфа', 'ижевск', 
                                               'киров', 'нижний', 'саранск', 'саров', 
                                               'нефтекамск', 'кемеров', 'новокузнецк',
                                               'новосибирск', 'северск', 'звенигов']):
        return 4000
    
    # Центральная Россия - 4500-5500 руб
    elif any(word in city_lower for word in ['воронеж', 'тверь', 'ярославль']):
        return 5000
    
    # Южное направление (Юг России, Кавказ) - 6000-7500 руб
    elif any(word in city_lower for word in ['волгоград', 'ростов', 'краснодар', 'сочи', 
                                               'адлер', 'кисловодск', 'владикавказ',
                                               'крым', 'севастополь']):
        return 6500
    
    # Дальние направления (Восток, Дальний Восток) - 7000-12000 руб
    elif any(word in city_lower for word in ['владивосток', 'улан', 'чита', 'енисейск']):
        return 8000
    
    # Очень дальние/труднодоступные направления - 7500-8500 руб
    elif any(word in city_lower for word in ['брест', 'калининград', 'североморск', 'алтай']):
        return 7500
    
    # По умолчанию - средняя цена
    else:
        return 5000

db = sqlite3.connect('calendar_plans.db')
cursor = db.cursor()

cursor.execute("""
    SELECT DISTINCT location 
    FROM events 
    WHERE event_type = 'Выездное' 
    ORDER BY location
""")

cities = cursor.fetchall()
db.close()

# Подготовка данных
cities_with_prices = []
total_estimate = 0

for city, in cities:
    price = estimate_price(city)
    total_estimate += price
    cities_with_prices.append({
        'город': city,
        'стоимость': price
    })

# Вывод на экран
print("Примерная стоимость детского билета в плацкарте (в одну сторону) от Нового Уренгоя")
print("=" * 90)
print(f"Всего направлений: {len(cities)}\n")

for i, city_data in enumerate(cities_with_prices, 1):
    print(f"{i:2}. {city_data['город']:35} - {city_data['стоимость']:>6,} руб.".replace(',', ' '))

print(f"\n{'=' * 90}")
print(f"Средняя стоимость билета: {total_estimate // len(cities):,} руб.".replace(',', ' '))
print(f"Общая сумма для всех направлений: {total_estimate:,} руб.".replace(',', ' '))

# Экспорт в CSV
csv_filename = 'cities_train_prices.csv'
with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['№', 'Город', 'Стоимость билета (руб)', 'Примечание'])
    writer.writeheader()
    
    for i, city_data in enumerate(cities_with_prices, 1):
        writer.writerow({
            '№': i,
            'Город': city_data['город'],
            'Стоимость билета (руб)': city_data['стоимость'],
            'Примечание': 'Детский плацкарт, в одну сторону'
        })

print(f"\nДанные экспортированы в файл: {csv_filename}")
print("\nПримечания:")
print("- Цены приблизительные, основаны на веб-поиске и расчетах по расстоянию")
print("- Детский билет обычно составляет 50% от стоимости взрослого")
print("- Фактическая стоимость зависит от даты, сезона и наличия мест")
print("- Рекомендуется уточнять цены на сайте РЖД (pass.rzd.ru) или у билетных агентств")
print("- Для некоторых направлений может потребоваться пересадка")

