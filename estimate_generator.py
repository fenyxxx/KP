# -*- coding: utf-8 -*-
"""
Генератор смет по шаблонам для выездных мероприятий
"""

import math


class EstimateGenerator:
    """Класс для автоматической генерации смет по шаблонам"""
    
    # Регионы с повышенной ставкой суточных (700 руб/день)
    HIGH_RATE_REGIONS = [
        'ЯНАО', 'Ямало-Ненецкий', 'Ямал',
        'ХМАО', 'Ханты-Мансийск', 'Югра',
        'Москва', 'Московская', 'Подмосковье',
        'Санкт-Петербург', 'СПб', 'Питер', 'Ленинградская'
    ]
    
    @staticmethod
    def get_daily_rate(location):
        """
        Определить ставку суточных в зависимости от региона
        
        Args:
            location: Место проведения мероприятия
            
        Returns:
            Ставка суточных (700 или 500 руб/день)
        """
        location_upper = location.upper()
        
        # Проверяем, относится ли регион к списку с повышенной ставкой
        for region in EstimateGenerator.HIGH_RATE_REGIONS:
            if region.upper() in location_upper:
                return 700  # ЯНАО, ХМАО, Москва, МО, СПб
        
        return 500  # Все остальные регионы
    
    @staticmethod
    def round_to_beautiful(value):
        """
        Округлить до красивого числа (заканчивается на 0)
        
        Args:
            value: Исходное значение
            
        Returns:
            Округленное значение
        """
        if value < 10:
            return round(value)
        elif value < 100:
            return round(value / 10) * 10
        elif value < 1000:
            return round(value / 50) * 50
        else:
            return round(value / 100) * 100
    
    @staticmethod
    def get_realistic_params(event):
        """
        Получить реалистичные параметры (дни и количество детей) в зависимости от вида спорта
        
        Args:
            event: Объект мероприятия
            
        Returns:
            (days, people_count) - количество дней и детей
        """
        import random
        
        # Количество дней от 1 до 7 (зависит от хэша названия для стабильности)
        hash_val = hash(event.name + event.location) % 100
        days = 1 + (hash_val % 7)  # от 1 до 7
        
        # Командные виды спорта
        team_sports = ['Футзал', 'Волейбол', 'Баскетбол', 'Гандбол']
        
        sport_upper = event.sport.upper()
        is_team_sport = any(sport.upper() in sport_upper for sport in team_sports)
        
        if is_team_sport:
            # Командные виды: от 6 до 14 человек
            min_people = 6
            max_people = 14
        else:
            # Остальные виды: от 1 до 14 человек
            min_people = 1
            max_people = 14
        
        # Используем хэш для стабильного случайного значения
        hash_people = hash(event.name + str(event.id)) % 100
        people_range = max_people - min_people + 1
        people_count = min_people + (hash_people % people_range)
        
        return days, people_count
    
    @staticmethod
    def generate_ppo_estimate(db, event, children_budget):
        """
        Создать смету на ППО (для детей) по шаблону
        ТОЧНО соответствует заложенному бюджету (100%)
        
        Args:
            db: Объект базы данных
            event: Объект мероприятия
            children_budget: Заложенная сумма на детей
            
        Returns:
            ID созданной сметы
        """
        if children_budget <= 0:
            # Создаём пустую смету
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
        
        # Получаем реалистичные параметры
        days_командировки, people_count = EstimateGenerator.get_realistic_params(event)
        days_proezd = 2  # туда и обратно
        
        # Определяем ставку суточных в зависимости от региона
        daily_rate = EstimateGenerator.get_daily_rate(event.location)
        
        # МИНИМАЛЬНЫЕ ТРЕБОВАНИЯ:
        min_prozhivanie_per_person = 1000  # минимум 1000 руб на проживание
        min_proezd_per_person = 300  # минимум 300 руб на человека за проезд
        
        # Рассчитываем минимально необходимую сумму
        min_prozhivanie_total = min_prozhivanie_per_person * people_count
        min_proezd_total = min_proezd_per_person * people_count * days_proezd
        
        # Пробуем с суточными
        sutochnie_total = people_count * days_командировки * daily_rate
        total_with_sutochnie = min_prozhivanie_total + min_proezd_total + sutochnie_total
        
        use_sutochnie = True
        
        if total_with_sutochnie > children_budget:
            # Не хватает денег - убираем суточные
            use_sutochnie = False
            sutochnie_total = 0
        
        # Распределяем бюджет
        if use_sutochnie:
            # С суточными
            remaining = children_budget - sutochnie_total
            
            # Проверяем минимумы
            if remaining >= (min_prozhivanie_total + min_proezd_total):
                # Можем соблюсти минимумы, делим остаток 50/50
                proezd_total = remaining * 0.5
                prozhivanie_total = remaining - proezd_total  # Для точности
                
                # Проверяем минимумы еще раз
                if proezd_total < min_proezd_total:
                    proezd_total = min_proezd_total
                    prozhivanie_total = remaining - proezd_total
                elif prozhivanie_total < min_prozhivanie_total:
                    prozhivanie_total = min_prozhivanie_total
                    proezd_total = remaining - prozhivanie_total
            else:
                # Выделяем минимумы
                proezd_total = min_proezd_total
                prozhivanie_total = remaining - proezd_total
        else:
            # Без суточных - весь бюджет на проезд и проживание
            if children_budget >= (min_prozhivanie_total + min_proezd_total):
                # Делим 50/50
                proezd_total = children_budget * 0.5
                prozhivanie_total = children_budget - proezd_total
                
                # Проверяем минимумы
                if proezd_total < min_proezd_total:
                    proezd_total = min_proezd_total
                    prozhivanie_total = children_budget - proezd_total
                elif prozhivanie_total < min_prozhivanie_total:
                    prozhivanie_total = min_prozhivanie_total
                    proezd_total = children_budget - prozhivanie_total
            else:
                # Выделяем минимумы по приоритету
                proezd_total = min(min_proezd_total, children_budget * 0.4)
                prozhivanie_total = children_budget - proezd_total
        
        # Рассчитываем ставки
        rate_proezd = round(proezd_total / (people_count * days_proezd), 2)
        rate_prozhivanie = round(prozhivanie_total / (people_count * days_командировки), 2)
        
        # ПРОЕЗД
        actual_proezd = rate_proezd * people_count * days_proezd
        db.add_estimate_item(
            estimate_id,
            'Проезд',
            description=f"маршрут: {event.location}",
            people_count=people_count,
            days_count=days_proezd,
            rate=rate_proezd
        )
        
        # СУТОЧНЫЕ (если используются)
        actual_sutochnie = 0
        if use_sutochnie:
            actual_sutochnie = daily_rate * people_count * days_командировки
            db.add_estimate_item(
                estimate_id,
                'Суточные',
                description=f"по территории ({daily_rate} руб/день)",
                people_count=people_count,
                days_count=days_командировки,
                rate=daily_rate
            )
        
        # ПРОЖИВАНИЕ - корректируем для ТОЧНОГО попадания в бюджет
        prozhivanie_corrected = children_budget - actual_proezd - actual_sutochnie
        rate_prozhivanie_corrected = round(prozhivanie_corrected / (people_count * days_командировки), 2)
        
        db.add_estimate_item(
            estimate_id,
            'Проживание',
            description="",
            people_count=people_count,
            days_count=days_командировки,
            rate=rate_prozhivanie_corrected
        )
        
        return estimate_id
    
    @staticmethod
    def generate_trainer_estimates(db, event, trainers_budget, trainers_count):
        """
        Создать сметы на тренеров (УЭВП) по шаблону
        ТОЧНО соответствует заложенному бюджету (100%)
        
        Args:
            db: Объект базы данных
            event: Объект мероприятия
            trainers_budget: Заложенная сумма на тренеров
            trainers_count: Количество тренеров
            
        Returns:
            Список ID созданных смет
        """
        estimate_ids = []
        
        if trainers_count == 0:
            return estimate_ids
        
        # Бюджет на одного тренера
        budget_per_trainer = trainers_budget / trainers_count if trainers_count > 0 else 0
        
        for i in range(trainers_count):
            trainer_name = f"тренер {i+1}"
            
            if budget_per_trainer <= 0:
                # Создаём пустую смету
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
            # Используем те же дни, что и для детей
            days_командировки, _ = EstimateGenerator.get_realistic_params(event)
            days_proezd = 2  # туда и обратно
            
            # Определяем ставку суточных в зависимости от региона
            daily_rate = EstimateGenerator.get_daily_rate(event.location)
            
            # МИНИМАЛЬНЫЕ ТРЕБОВАНИЯ (на 1 человека):
            min_prozhivanie_total = 1000 * people_count  # минимум 1000 руб
            min_proezd_total = 300 * people_count * days_proezd  # минимум 300 руб за проезд
            
            # Пробуем с суточными
            sutochnie_total = people_count * days_командировки * daily_rate
            total_with_sutochnie = min_prozhivanie_total + min_proezd_total + sutochnie_total
            
            use_sutochnie = True
            
            if total_with_sutochnie > budget_per_trainer:
                # Не хватает денег - убираем суточные
                use_sutochnie = False
                sutochnie_total = 0
            
            # Распределяем бюджет
            if use_sutochnie:
                # С суточными
                remaining = budget_per_trainer - sutochnie_total
                
                # Проверяем минимумы
                if remaining >= (min_prozhivanie_total + min_proezd_total):
                    # Можем соблюсти минимумы, делим остаток 50/50
                    proezd_total = remaining * 0.5
                    prozhivanie_total = remaining - proezd_total  # Для точности
                    
                    # Проверяем минимумы еще раз
                    if proezd_total < min_proezd_total:
                        proezd_total = min_proezd_total
                        prozhivanie_total = remaining - proezd_total
                    elif prozhivanie_total < min_prozhivanie_total:
                        prozhivanie_total = min_prozhivanie_total
                        proezd_total = remaining - prozhivanie_total
                else:
                    # Выделяем минимумы
                    proezd_total = min_proezd_total
                    prozhivanie_total = remaining - proezd_total
            else:
                # Без суточных - весь бюджет на проезд и проживание
                if budget_per_trainer >= (min_prozhivanie_total + min_proezd_total):
                    # Делим 50/50
                    proezd_total = budget_per_trainer * 0.5
                    prozhivanie_total = budget_per_trainer - proezd_total
                    
                    # Проверяем минимумы
                    if proezd_total < min_proezd_total:
                        proezd_total = min_proezd_total
                        prozhivanie_total = budget_per_trainer - proezd_total
                    elif prozhivanie_total < min_prozhivanie_total:
                        prozhivanie_total = min_prozhivanie_total
                        proezd_total = budget_per_trainer - prozhivanie_total
                else:
                    # Выделяем минимумы по приоритету
                    proezd_total = min(min_proezd_total, budget_per_trainer * 0.4)
                    prozhivanie_total = budget_per_trainer - proezd_total
            
            # Рассчитываем ставки
            rate_proezd = round(proezd_total / (people_count * days_proezd), 2)
            
            # ПРОЕЗД
            actual_proezd = rate_proezd * people_count * days_proezd
            db.add_estimate_item(
                estimate_id,
                'Проезд',
                description=f"маршрут: {event.location}",
                people_count=people_count,
                days_count=days_proezd,
                rate=rate_proezd
            )
            
            # СУТОЧНЫЕ (если используются)
            actual_sutochnie = 0
            if use_sutochnie:
                actual_sutochnie = daily_rate * people_count * days_командировки
                db.add_estimate_item(
                    estimate_id,
                    'Суточные',
                    description=f"по территории ({daily_rate} руб/день)",
                    people_count=people_count,
                    days_count=days_командировки,
                    rate=daily_rate
                )
            
            # ПРОЖИВАНИЕ - корректируем для ТОЧНОГО попадания в бюджет
            prozhivanie_corrected = budget_per_trainer - actual_proezd - actual_sutochnie
            rate_prozhivanie_corrected = round(prozhivanie_corrected / (people_count * days_командировки), 2)
            
            db.add_estimate_item(
                estimate_id,
                'Проживание',
                description="",
                people_count=people_count,
                days_count=days_командировки,
                rate=rate_prozhivanie_corrected
            )
            
            estimate_ids.append(estimate_id)
        
        return estimate_ids
    
    @staticmethod
    def auto_generate_estimates(db, event):
        """
        Автоматически создать все сметы для выездного мероприятия
        
        Args:
            db: Объект базы данных
            event: Объект мероприятия
            
        Returns:
            Кортеж (ppo_estimate_id, trainer_estimate_ids)
        """
        if event.event_type != "Выездное":
            return None, []
        
        # Создаём смету на ППО
        ppo_estimate_id = EstimateGenerator.generate_ppo_estimate(
            db, event, event.children_budget
        )
        
        # Создаём сметы на тренеров
        trainer_estimate_ids = EstimateGenerator.generate_trainer_estimates(
            db, event, event.trainers_budget, event.trainers_count
        )
        
        return ppo_estimate_id, trainer_estimate_ids

