# -*- coding: utf-8 -*-
import sqlite3

db = sqlite3.connect('calendar_plans.db')
cursor = db.cursor()
cursor.execute("SELECT DISTINCT location FROM events WHERE event_type = 'Выездное' ORDER BY location")
cities = [c[0] for c in cursor.fetchall()]
db.close()

html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Список городов для выездных мероприятий</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #0066B3;
        }}
        .info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .cities {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .city {{
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <h1>📍 Список городов для выездных мероприятий</h1>
    <div class="info">
        <strong>Всего уникальных городов:</strong> {len(cities)}
    </div>
    <div class="cities">
'''

for i, city in enumerate(cities, 1):
    html += f'        <div class="city">{i}. {city}</div>\n'

html += '''    </div>
</body>
</html>
'''

with open('CITIES_FULL_LIST.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("OK")

