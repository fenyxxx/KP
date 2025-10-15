# -*- coding: utf-8 -*-
import sqlite3
import sys

# Принудительно выставляем кодировку
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

try:
    db = sqlite3.connect('calendar_plans.db')
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT location FROM events WHERE event_type = 'Выездное' ORDER BY location")
    cities = [c[0] for c in cursor.fetchall()]
    db.close()
    
    # Выводим Python код
    print("# Города для выездных мероприятий")
    print(f"# Всего: {len(cities)}")
    print("CITIES = [")
    for city in cities:
        print(f'    "{city}",')
    print("]")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)

