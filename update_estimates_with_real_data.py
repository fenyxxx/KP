# -*- coding: utf-8 -*-
"""
Обновление смет на основе реальных данных о стоимости проезда и проживания
"""

import sqlite3
from database import Database
from models import Event
import random
import math


def round_up_to_10(value):
    """
    Округлить в большую сторону до 10
    Например: 1001 -> 1010, 1005 -> 1010, 1010 -> 1010
    """
    return math.ceil(value / 10) * 10

# Справочник реальных данных о городах
CITY_DATA = {
    'г Нижневартовск': {'transport': 'жд', 'proezd': 2000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (2, 4)},
    'г. Барнаул': {'transport': 'жд', 'proezd': 3000, 'prozhivanie': 1000, 'sutochnie': 500, 'days_range': (3, 5)},
    'г. Бердск': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 5)},
    'г. Берёзовский': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 5)},
    'г. Верхняя Пышма': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 6)},
    'г. Волгоград': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Губкинский': {'transport': 'жд', 'proezd': 1500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 5)},
    'г. Екатеринбург': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (2, 5)},
    'г. Еакатеринбург': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (2, 5)},
    'г. Екаткринбург': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (2, 5)},
    'г. Казань': {'transport': 'жд', 'proezd': 7000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Каменск-Уральский': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Когалым': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Красногорск': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 6)},
    'г. Кстово': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Лобня': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (3, 6)},
    'г. Магнитогорск': {'transport': 'жд', 'proezd': 10000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 6)},
    'г. Майкоп': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Медногорск': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Москва': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (2, 5)},
    'г. Муравленко': {'transport': 'жд', 'proezd': 2000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (2, 6)},
    'г. Надым': {'transport': 'жд', 'proezd': 2000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (1, 5)},
    'Надым': {'transport': 'жд', 'proezd': 2000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (1, 5)},
    'г. Невинномыск': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Нижневартовск': {'transport': 'жд', 'proezd': 2500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 7)},
    'г. Нижний Новгород': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Нижний Тагил': {'transport': 'жд', 'proezd': 7000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Новый Уренгой': {'transport': 'жд', 'proezd': 0, 'prozhivanie': 0, 'sutochnie': 0, 'days_range': (1, 2)},  # Местное
    'г. Ноябрьск': {'transport': 'жд', 'proezd': 2500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 7)},
    'Ноябрьск': {'transport': 'жд', 'proezd': 2500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 7)},
    'г. Пыть-Ях': {'transport': 'жд', 'proezd': 3000, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 7)},
    'г. Ревда': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Салехард': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 2000, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Санкт-Петербург': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (3, 7)},
    'г.Санкт-Петербург': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (3, 7)},
    'г.Санкт Петербург': {'transport': 'авиа', 'proezd': 12000, 'prozhivanie': 2000, 'sutochnie': 700, 'days_range': (3, 7)},
    'г. Саратов': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Славянск-на Кубани': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Славянск-на-Кубани': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Сургут': {'transport': 'жд', 'proezd': 3000, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 5)},
    'г. Тарко-Сале': {'transport': 'жд', 'proezd': 1500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 5)},
    'г. Тюмень': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Челябинск': {'transport': 'жд', 'proezd': 3500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г. Ялуторовск': {'transport': 'жд', 'proezd': 3000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'п. Кабардинка': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (7, 21)},
    'п. Пангоды': {'transport': 'жд', 'proezd': 1500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (1, 4)},
    'п. Приобье ХМАО': {'transport': 'жд', 'proezd': 2500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (3, 7)},
    'по назначению': {'transport': 'жд', 'proezd': 5000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (1, 7)},
    'с. Уват': {'transport': 'жд', 'proezd': 3000, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (3, 7)},
    'с Усинск': {'transport': 'жд', 'proezd': 3000, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (3, 7)},
    'Волгоград': {'transport': 'авиа', 'proezd': 15000, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
    'г Нижневартовск': {'transport': 'жд', 'proezd': 2500, 'prozhivanie': 1500, 'sutochnie': 700, 'days_range': (2, 7)},
    'Брест': {'transport': 'жд', 'proezd': 7500, 'prozhivanie': 1500, 'sutochnie': 500, 'days_range': (3, 7)},
}


def normalize_city_name(location):
    """Нормализация названия города для поиска в справочнике"""
    # Пробуем найти точное совпадение
    if location in CITY_DATA:
        return location
    
    # Пробуем найти похожее название (без учета точек и пробелов)
    location_normalized = location.replace('.', '').replace(' ', '').lower()
    for city_key in CITY_DATA.keys():
        city_key_normalized = city_key.replace('.', '').replace(' ', '').lower()
        if location_normalized == city_key_normalized or location_normalized in city_key_normalized:
            return city_key
    
    # Не нашли - вернем исходное
    return None


def get_city_data(location):
    """Получить данные о городе из справочника"""
    city_key = normalize_city_name(location)
    
    if city_key and city_key in CITY_DATA:
        return CITY_DATA[city_key]
    
    # Данные по умолчанию для неизвестных городов
    return {
        'transport': 'жд',
        'proezd': 5000,
        'prozhivanie': 1500,
        'sutochnie': 500,
        'days_range': (3, 7)
    }


def get_days_for_event(event, city_data):
    """Получить количество дней для мероприятия"""
    days_min, days_max = city_data['days_range']
    
    # Используем хэш для стабильного "случайного" значения
    hash_val = hash(f"{event.name}_{event.location}_{event.id}") % 100
    days_range = days_max - days_min + 1
    days = days_min + (hash_val % days_range)
    
    return days


def generate_realistic_ppo_estimate(db, event, children_budget, city_data, days):
    """
    Создать реалистичную смету на ППО с использованием реальных данных
    """
    if children_budget <= 0:
        estimate_id = db.create_estimate(
            event.id,
            'ППО',
            approved_by="Председатель ППО Газпром добыча Ямбург профсоюз",
            place=event.location,
            start_date="",
            end_date=""
        )
        return estimate_id
    
    # Создаём смету
    estimate_id = db.create_estimate(
        event.id,
        'ППО',
        approved_by="Председатель ППО Газпром добыча Ямбург профсоюз",
        place=event.location,
        start_date="",
        end_date=""
    )
    
    # Получаем данные из справочника
    proezd_rate = city_data['proezd']
    prozhivanie_rate = city_data['prozhivanie']
    sutochnie_rate = city_data['sutochnie']
    
    # Определяем количество детей на основе бюджета
    # Формула: дети = бюджет / (проезд*2 + проживание*дни + суточные*дни)
    cost_per_child_with_sutochnie = (proezd_rate * 2) + (prozhivanie_rate * days) + (sutochnie_rate * days)
    people_count = int(children_budget / cost_per_child_with_sutochnie)
    
    # Минимум 1 ребенок, максимум 14
    people_count = max(1, min(14, people_count))
    
    # Проверяем, хватит ли на суточные
    total_proezd = people_count * 2 * proezd_rate
    total_prozhivanie = people_count * days * prozhivanie_rate
    total_sutochnie = people_count * days * sutochnie_rate
    
    total_with_sutochnie = total_proezd + total_prozhivanie + total_sutochnie
    
    use_sutochnie = total_with_sutochnie <= children_budget
    
    if not use_sutochnie:
        # Убираем суточные и пересчитываем количество детей
        cost_per_child_without_sutochnie = (proezd_rate * 2) + (prozhivanie_rate * days)
        people_count = int(children_budget / cost_per_child_without_sutochnie)
        people_count = max(1, min(14, people_count))
        
        total_proezd = people_count * 2 * proezd_rate
        total_prozhivanie = people_count * days * prozhivanie_rate
        total_sutochnie = 0
    
    # Корректируем для точного попадания в бюджет
    total_calculated = total_proezd + total_prozhivanie + total_sutochnie
    
    if total_calculated > children_budget:
        # Урежаем проживание
        total_prozhivanie = children_budget - total_proezd - total_sutochnie
        if total_prozhivanie < 0:
            total_prozhivanie = 0
            total_proezd = children_budget
        prozhivanie_rate = round(total_prozhivanie / (people_count * days), 2) if people_count * days > 0 else 0
    elif total_calculated < children_budget:
        # Добавляем в проживание
        diff = children_budget - total_calculated
        total_prozhivanie += diff
        prozhivanie_rate = round(total_prozhivanie / (people_count * days), 2) if people_count * days > 0 else 0
    
    # Добавляем статьи в смету
    
    # 1. ПРОЕЗД
    if proezd_rate > 0:
        db.add_estimate_item(
            estimate_id,
            'Проезд',
            description=f"маршрут: {event.location} ({city_data['transport']})",
            people_count=people_count,
            days_count=2,  # туда и обратно
            rate=proezd_rate
        )
    
    # 2. СУТОЧНЫЕ (если используются)
    if use_sutochnie and sutochnie_rate > 0:
        db.add_estimate_item(
            estimate_id,
            'Суточные',
            description=f"по территории ({sutochnie_rate} руб/день)",
            people_count=people_count,
            days_count=days,
            rate=sutochnie_rate
        )
    
    # 3. ПРОЖИВАНИЕ
    if prozhivanie_rate > 0:
        db.add_estimate_item(
            estimate_id,
            'Проживание',
            description="",
            people_count=people_count,
            days_count=days,
            rate=prozhivanie_rate
        )
    
    return estimate_id


def generate_realistic_trainer_estimates(db, event, trainers_list, city_data, days):
    """
    Создать реалистичные сметы на тренеров с использованием реальных данных
    """
    estimate_ids = []
    
    if not trainers_list:
        return estimate_ids
    
    # Получаем данные из справочника
    proezd_rate = city_data['proezd']
    prozhivanie_rate = city_data['prozhivanie']
    sutochnie_rate = city_data['sutochnie']
    
    for trainer in trainers_list:
        trainer_name = trainer.get('name', 'тренер')
        budget = trainer.get('budget', 0)
        
        if budget <= 0:
            estimate_id = db.create_estimate(
                event.id,
                'УЭВП',
                trainer_name=trainer_name,
                approved_by="Зам. начальника ф УЭВП по СОиКМР",
                place=event.location,
                start_date="",
                end_date=""
            )
            estimate_ids.append(estimate_id)
            continue
        
        # Создаём смету для тренера
        estimate_id = db.create_estimate(
            event.id,
            'УЭВП',
            trainer_name=trainer_name,
            approved_by="Зам. начальника ф УЭВП по СОиКМР",
            place=event.location,
            start_date="",
            end_date=""
        )
        
        people_count = 1  # один тренер
        
        # Проверяем, хватит ли на суточные
        total_proezd = people_count * 2 * proezd_rate
        total_prozhivanie = people_count * days * prozhivanie_rate
        total_sutochnie = people_count * days * sutochnie_rate
        
        total_with_sutochnie = total_proezd + total_prozhivanie + total_sutochnie
        
        use_sutochnie = total_with_sutochnie <= budget
        
        if not use_sutochnie:
            total_sutochnie = 0
        
        # Корректируем для точного попадания в бюджет
        total_calculated = total_proezd + total_prozhivanie + total_sutochnie
        
        if total_calculated > budget:
            # Урежаем проживание
            total_prozhivanie = budget - total_proezd - total_sutochnie
            if total_prozhivanie < 0:
                total_prozhivanie = 0
                total_proezd = budget
            prozhivanie_rate_corrected = round(total_prozhivanie / (people_count * days), 2) if days > 0 else 0
        elif total_calculated < budget:
            # Добавляем в проживание
            diff = budget - total_calculated
            total_prozhivanie += diff
            prozhivanie_rate_corrected = round(total_prozhivanie / (people_count * days), 2) if days > 0 else 0
        else:
            prozhivanie_rate_corrected = prozhivanie_rate
        
        # Добавляем статьи в смету
        
        # 1. ПРОЕЗД
        if proezd_rate > 0:
            db.add_estimate_item(
                estimate_id,
                'Проезд',
                description=f"маршрут: {event.location} ({city_data['transport']})",
                people_count=people_count,
                days_count=2,
                rate=proezd_rate
            )
        
        # 2. СУТОЧНЫЕ (если используются)
        if use_sutochnie and sutochnie_rate > 0:
            db.add_estimate_item(
                estimate_id,
                'Суточные',
                description=f"по территории ({sutochnie_rate} руб/день)",
                people_count=people_count,
                days_count=days,
                rate=sutochnie_rate
            )
        
        # 3. ПРОЖИВАНИЕ
        if prozhivanie_rate_corrected > 0:
            db.add_estimate_item(
                estimate_id,
                'Проживание',
                description="",
                people_count=people_count,
                days_count=days,
                rate=prozhivanie_rate_corrected
            )
        
        estimate_ids.append(estimate_id)
    
    return estimate_ids


def update_all_estimates():
    """Обновить все сметы для выездных мероприятий"""
    db = Database()
    
    # Получаем все годы
    years = db.get_all_years()
    
    if not years:
        print("Нет данных в базе")
        return
    
    total_updated = 0
    
    for year in years:
        print(f"\nОбрабатываем год: {year}")
        events_data = db.get_events_by_year(year)
        
        for event_data in events_data:
            event = Event.from_db_row(event_data)
            
            # Обрабатываем только выездные мероприятия
            if event.event_type != "Выездное":
                continue
            
            print(f"  Обрабатываем: {event.name} ({event.location})")
            
            # Получаем данные о городе
            city_data = get_city_data(event.location)
            days = get_days_for_event(event, city_data)
            
            print(f"    Город: {event.location}, Дней: {days}, Транспорт: {city_data['transport']}")
            
            # Удаляем старые сметы
            old_estimates = db.get_estimates_by_event(event.id)
            for old_estimate in old_estimates:
                db.delete_estimate(old_estimate[0])
            
            # Создаём новую смету на ППО
            if event.children_budget > 0:
                ppo_estimate_id = generate_realistic_ppo_estimate(
                    db, event, event.children_budget, city_data, days
                )
                print(f"    [+] Создана смета ППО (ID: {ppo_estimate_id})")
            
            # Создаём новые сметы на тренеров
            if event.trainers_list and len(event.trainers_list) > 0:
                trainer_estimate_ids = generate_realistic_trainer_estimates(
                    db, event, event.trainers_list, city_data, days
                )
                print(f"    [+] Создано смет УЭВП: {len(trainer_estimate_ids)}")
            
            total_updated += 1
    
    db.close()
    
    print(f"\n{'='*70}")
    print(f"Обработано мероприятий: {total_updated}")
    print(f"Все сметы успешно обновлены на основе реальных данных!")
    print(f"{'='*70}")


if __name__ == "__main__":
    print("="*70)
    print("ОБНОВЛЕНИЕ СМЕТ НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ")
    print("="*70)
    
    update_all_estimates()

