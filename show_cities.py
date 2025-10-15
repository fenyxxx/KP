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

cities = cursor.fetchall()
db.close()

print(f"Всего городов: {len(cities)}\n")

for i, (city,) in enumerate(cities, 1):
    print(f"{i}. {city}")

