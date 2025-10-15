# -*- coding: utf-8 -*-
"""Список городов - генерируется при первом запуске"""

import sqlite3
import os

# Проверяем, нужно ли генерировать список
_CITIES_CACHE = None

def get_cities():
    global _CITIES_CACHE
    
    if _CITIES_CACHE is not None:
        return _CITIES_CACHE
    
    db_path = 'calendar_plans.db'
    if not os.path.exists(db_path):
        return []
    
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT DISTINCT location 
        FROM events 
        WHERE event_type = 'Выездное' 
        ORDER BY location
    """)
    
    _CITIES_CACHE = [city[0] for city in cursor.fetchall()]
    db.close()
    
    return _CITIES_CACHE

if __name__ == '__main__':
    cities = get_cities()
    print(f"Всего городов: {len(cities)}\n")
    for i, city in enumerate(cities, 1):
        print(f"{i}. {city}")

