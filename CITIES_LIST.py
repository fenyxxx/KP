# -*- coding: utf-8 -*-
"""
Список всех городов для выездных мероприятий
Сгенерировано автоматически из базы данных
"""

# Запускаем генерацию списка
if __name__ != '__main__':
    # Этот код выполнится при импорте
    pass
else:
    # Генерация списка при запуске скрипта
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
    
    # Создаем новый файл с данными
    content = '''# -*- coding: utf-8 -*-
"""
Список всех городов для выездных мероприятий
"""

CITIES = [
'''
    
    for city in cities:
        content += f'    "{city}",\n'
    
    content += ''']

if __name__ == '__main__':
    print(f"Всего городов: {len(CITIES)}")
    print("\\nСписок городов:\\n")
    for i, city in enumerate(CITIES, 1):
        print(f"{i}. {city}")
'''
    
    with open('CITIES_LIST.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Файл обновлен. Всего городов: {len(cities)}")

