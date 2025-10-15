# -*- coding: utf-8 -*-
import sqlite3

db = sqlite3.connect('calendar_plans.db')
cursor = db.cursor()
cursor.execute("SELECT DISTINCT location FROM events WHERE event_type = 'Выездное' ORDER BY location")
cities = [c[0] for c in cursor.fetchall()]
db.close()

# Создаем готовый ответ пользователю
response = f"""
📍 **СПИСОК ГОРОДОВ ДЛЯ ВЫЕЗДНЫХ МЕРОПРИЯТИЙ**
Всего уникальных городов: {len(cities)}

"""

for i, city in enumerate(cities, 1):
    response += f"{i}. {city}\n"

# Сохраняем как Python переменную в новый файл
with open('CITY_NAMES.txt', 'w', encoding='utf-8') as f:
    f.write(response)

# Также создаем Python-список
py_code = "# Города\\nCITIES = [\\n"
for city in cities:
    py_code += f'    "{city}",\\n'
py_code += "]"

with open('cities_list_code.txt', 'w', encoding='utf-8') as f:
    f.write(py_code)

print(len(cities))  # Просто выводим количество

