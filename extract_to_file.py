# -*- coding: utf-8 -*-
import sqlite3
import sys
import io

# Меняем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# Выводим в формате для copy-paste
print("="*60)
print(f"СПИСОК ГОРОДОВ ДЛЯ ВЫЕЗДНЫХ МЕРОПРИЯТИЙ ({len(cities)} шт.)")
print("="*60)
print()

for i, (city,) in enumerate(cities, 1):
    print(f"{i}. {city}")

print()
print("="*60)

