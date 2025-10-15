# -*- coding: utf-8 -*-
import sqlite3

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

# Создаем Python-файл со списком
code = f'''# -*- coding: utf-8 -*-
"""
Список городов для выездных мероприятий
Всего: {len(cities)} городов
"""

CITIES_DATA = [
'''

for city in cities:
    # Экранируем кавычки
    escaped_city = city.replace('"', '\\"')
    code += f'    "{escaped_city}",\n'

code += '''
]

if __name__ == '__main__':
    print(f"Всего городов: {len(CITIES_DATA)}")
    print()
    for i, city in enumerate(CITIES_DATA, 1):
        print(f"{i}. {city}")
'''

# Сохраняем
with open('CITIES_DATA.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("OK")

