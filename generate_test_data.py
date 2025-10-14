# -*- coding: utf-8 -*-
"""
Скрипт для генерации тестовых данных на 2025 год
"""

import random
from datetime import datetime, timedelta
from database import Database
from constants import SPORTS, MONTHS

def generate_test_data():
    """Генерация тестовых мероприятий на 2025 год"""
    
    db = Database()
    
    # Очищаем старые данные 2025 года (если есть)
    print("Очистка старых данных 2025 года...")
    db.cursor.execute("DELETE FROM events WHERE year = 2025")
    db.connection.commit()
    
    # Параметры генерации
    total_events = random.randint(80, 120)
    internal_count = int(total_events * 0.1)  # 10% внутренние
    external_count = total_events - internal_count  # 90% выездные
    
    print(f"Генерация {total_events} мероприятий ({internal_count} внутренних, {external_count} выездных)...")
    
    # Примеры названий соревнований
    event_templates = {
        'Бокс': [
            "Первенство ДЮСК по боксу",
            "Открытое первенство города",
            "Турнир памяти {name}",
            "Кубок ЯНАО по боксу",
            "Межрегиональный турнир",
            "Первенство Уральского ФО"
        ],
        'Волейбол': [
            "Первенство ДЮСК по волейболу",
            "Кубок города среди юношей",
            "Открытое первенство ЯНАО",
            "Турнир памяти {name}",
            "Межрегиональные соревнования",
            "Финал первенства УФО"
        ],
        'Киокусинкай': [
            "Первенство ДЮСК по киокусинкай",
            "Открытый турнир по каратэ",
            "Кубок Ямала",
            "Межрегиональный турнир",
            "Первенство УФО",
            "Всероссийские соревнования"
        ],
        'Лыжные гонки': [
            "Первенство ДЮСК по лыжным гонкам",
            "Открытые соревнования",
            "Кубок города",
            "Первенство ЯНАО",
            "Межрегиональная гонка",
            "Финал первенства России"
        ],
        'Настольный тенис': [
            "Первенство ДЮСК по настольному теннису",
            "Открытый турнир",
            "Кубок города",
            "Первенство ЯНАО",
            "Межрегиональный турнир",
            "Финал УФО"
        ],
        'Плавание': [
            "Первенство ДЮСК по плаванию",
            "Открытые соревнования",
            "Кубок Ямала",
            "Первенство ЯНАО",
            "Межрегиональный турнир",
            "Всероссийские соревнования"
        ],
        'Танцевальный спорт': [
            "Первенство ДЮСК по танцевальному спорту",
            "Открытый турнир",
            "Кубок города",
            "Первенство ЯНАО",
            "Межрегиональный фестиваль",
            "Финал России"
        ],
        'Футзал': [
            "Первенство ДЮСК по футзалу",
            "Открытое первенство города",
            "Кубок Ямала",
            "Первенство ЯНАО",
            "Межрегиональный турнир",
            "Финал первенства УФО"
        ]
    }
    
    # Города для выездных соревнований
    cities = [
        "г. Салехард", "г. Новый Уренгой", "г. Губкинский", "г. Надым", 
        "г. Ноябрьск", "г. Тюмень", "г. Екатеринбург", "г. Челябинск",
        "г. Пермь", "г. Сургут", "г. Нижневартовск", "г. Когалым",
        "г. Уфа", "г. Казань", "г. Москва", "г. Санкт-Петербург"
    ]
    
    # Имена для турниров памяти
    memorial_names = [
        "Героя России", "ветерана спорта", "тренера Иванова",
        "заслуженного мастера спорта", "Олимпийского чемпиона"
    ]
    
    events_data = []
    
    # Генерируем внутренние мероприятия
    for i in range(internal_count):
        sport = random.choice(SPORTS)
        month = random.choice(MONTHS)
        
        # Название
        template = random.choice(event_templates[sport])
        if '{name}' in template:
            name = template.format(name=random.choice(memorial_names))
        else:
            name = template
        
        # Место проведения - всегда СОК или спортзалы в городе
        locations = ["СОК", "Спортзал ДЮСК", "Спортзал №5", "Ледовая арена"]
        location = random.choice(locations)
        
        # Финансирование - только на детей
        children_budget = random.randint(5, 30) * 1000  # От 5 до 30 тысяч
        trainers_budget = 0
        trainers_count = random.randint(1, 3)
        
        events_data.append({
            'sport': sport,
            'event_type': 'Внутреннее',
            'month': month,
            'name': name,
            'location': location,
            'children_budget': children_budget,
            'trainers_budget': trainers_budget,
            'trainers_count': trainers_count
        })
    
    # Генерируем выездные мероприятия
    external_with_only_trainers = int(external_count * 0.3)  # 30% с финансированием только тренеров
    
    for i in range(external_count):
        sport = random.choice(SPORTS)
        month = random.choice(MONTHS)
        
        # Название
        template = random.choice(event_templates[sport])
        if '{name}' in template:
            name = template.format(name=random.choice(memorial_names))
        else:
            name = template
        
        # Место проведения - случайный город
        location = random.choice(cities)
        
        # Финансирование
        if i < external_with_only_trainers:
            # Только тренеры
            children_budget = 0
            trainers_budget = random.randint(15, 60) * 1000  # От 15 до 60 тысяч
        else:
            # Оба бюджета
            children_budget = random.randint(50, 250) * 1000  # От 50 до 250 тысяч
            trainers_budget = random.randint(15, 60) * 1000  # От 15 до 60 тысяч
        
        trainers_count = random.randint(1, 4)
        
        events_data.append({
            'sport': sport,
            'event_type': 'Выездное',
            'month': month,
            'name': name,
            'location': location,
            'children_budget': children_budget,
            'trainers_budget': trainers_budget,
            'trainers_count': trainers_count
        })
    
    # Перемешиваем мероприятия
    random.shuffle(events_data)
    
    # Определяем какие мероприятия будут проведены (80%), отменены (5%), запланированы (15%)
    conducted_count = int(len(events_data) * 0.8)
    cancelled_count = int(len(events_data) * 0.05)
    
    # Выбираем индексы
    all_indices = list(range(len(events_data)))
    random.shuffle(all_indices)
    
    conducted_indices = all_indices[:conducted_count]
    cancelled_indices = all_indices[conducted_count:conducted_count + cancelled_count]
    # Остальные будут запланированы
    
    # Вставляем данные в БД
    print("Вставка данных в базу...")
    
    # Месяца для генерации дат
    month_numbers = {
        'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4,
        'Май': 5, 'Июнь': 6, 'Июль': 7, 'Август': 8,
        'Сентябрь': 9, 'Октябрь': 10, 'Ноябрь': 11, 'Декабрь': 12
    }
    
    for idx, event in enumerate(events_data):
        # Базовые данные
        year = 2025
        sport = event['sport']
        event_type = event['event_type']
        name = event['name']
        location = event['location']
        month = event['month']
        children_budget = event['children_budget']
        trainers_budget = event['trainers_budget']
        trainers_count = event['trainers_count']
        notes = ""
        
        # Статус и фактические данные
        if idx in conducted_indices:
            status = "Проведено"
            
            # Генерируем даты
            month_num = month_numbers[month]
            day_start = random.randint(1, 25)
            duration = random.randint(1, 3)  # 1-3 дня
            
            try:
                start_date = datetime(2025, month_num, day_start)
                end_date = start_date + timedelta(days=duration)
                actual_start_date = start_date.strftime('%d.%m.%Y')
                actual_end_date = end_date.strftime('%d.%m.%Y')
            except:
                # На случай невалидной даты
                actual_start_date = f"15.{month_num:02d}.2025"
                actual_end_date = f"17.{month_num:02d}.2025"
            
            # Фактические расходы с отклонением ±20%
            if children_budget > 0:
                deviation = random.uniform(-0.2, 0.2)
                actual_children_budget = children_budget * (1 + deviation)
                actual_children_budget = round(actual_children_budget, 2)
            else:
                actual_children_budget = None
            
            if trainers_budget > 0:
                deviation = random.uniform(-0.2, 0.2)
                actual_trainers_budget = trainers_budget * (1 + deviation)
                actual_trainers_budget = round(actual_trainers_budget, 2)
            else:
                actual_trainers_budget = None
            
            cancellation_reason = None
            postponement_reason = None
            
        elif idx in cancelled_indices:
            # Отменено (5%)
            status = "Отменено"
            actual_start_date = None
            actual_end_date = None
            actual_children_budget = None
            actual_trainers_budget = None
            
            # Причины отмены
            cancellation_reasons = [
                "Отсутствие финансирования",
                "Недостаточное количество участников",
                "Болезнь тренера",
                "Неблагоприятные погодные условия",
                "Отказ принимающей стороны",
                "Карантинные мероприятия",
                "Технические причины (неисправность оборудования)"
            ]
            cancellation_reason = random.choice(cancellation_reasons)
            postponement_reason = None
            
        else:
            # Запланировано (15%)
            status = "Запланировано"
            actual_start_date = None
            actual_end_date = None
            actual_children_budget = None
            actual_trainers_budget = None
            cancellation_reason = None
            postponement_reason = None
        
        # Вставка в БД
        db.cursor.execute('''
            INSERT INTO events (
                year, sport, event_type, name, location, month,
                children_budget, trainers_count, trainers_budget, notes,
                status, actual_start_date, actual_end_date,
                actual_children_budget, actual_trainers_budget,
                cancellation_reason, postponement_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            year, sport, event_type, name, location, month,
            children_budget, trainers_count, trainers_budget, notes,
            status, actual_start_date, actual_end_date,
            actual_children_budget, actual_trainers_budget,
            cancellation_reason, postponement_reason
        ))
    
    db.connection.commit()
    
    planned_count = len(events_data) - conducted_count - cancelled_count
    
    print(f"\nУспешно создано {len(events_data)} мероприятий на 2025 год!")
    print(f"  - Внутренних: {internal_count}")
    print(f"  - Выездных: {external_count}")
    print(f"  - Проведено: {conducted_count} ({conducted_count/len(events_data)*100:.1f}%)")
    print(f"  - Отменено: {cancelled_count} ({cancelled_count/len(events_data)*100:.1f}%)")
    print(f"  - Запланировано: {planned_count} ({planned_count/len(events_data)*100:.1f}%)")
    
    # Статистика по видам спорта
    print("\nРаспределение по видам спорта:")
    sport_counts = {}
    for event in events_data:
        sport = event['sport']
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
    
    for sport in sorted(sport_counts.keys()):
        print(f"  {sport}: {sport_counts[sport]}")
    
    db.close()
    print("\nГотово! Откройте программу и выберите 2025 год.")

if __name__ == "__main__":
    print("=" * 60)
    print("ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ НА 2025 ГОД")
    print("=" * 60)
    print()
    
    generate_test_data()

