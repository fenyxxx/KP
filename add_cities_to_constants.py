# -*- coding: utf-8 -*-
import sqlite3

# Извлекаем города
db = sqlite3.connect('calendar_plans.db')
cursor = db.cursor()

cursor.execute("""
    SELECT DISTINCT location 
    FROM events 
    WHERE event_type = 'Выездное' 
    ORDER BY location
""")

cities = [city[0] for city in cursor.fetchall()]
db.close()

# Читаем текущий constants.py
with open('constants.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем, нет ли уже списка CITIES
if 'CITIES = [' in content:
    print("CITIES уже есть в constants.py")
else:
    # Добавляем список городов
    cities_code = '\n# Города для выездных мероприятий\nCITIES = [\n'
    for city in cities:
        escaped_city = city.replace('"', '\\"').replace("'", "\\'")
        cities_code += f'    "{escaped_city}",\n'
    cities_code += ']\n'
    
    # Добавляем в конец файла
    with open('constants.py', 'a', encoding='utf-8') as f:
        f.write(cities_code)
    
    print(f"Добавлено {len(cities)} городов в constants.py")

