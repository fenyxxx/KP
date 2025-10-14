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
    def generate_ppo_estimate(db, event, children_budget):
        """
        Создать смету на ППО (для детей) по шаблону
        
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
        
        # Примерное количество детей (по умолчанию 10-15)
        people_count = 12
        
        # Определяем ставку суточных в зависимости от региона
        daily_rate = EstimateGenerator.get_daily_rate(event.location)
        
        # Примерное количество дней командировки
        days_командировки = 5
        
        # Рассчитываем сумму на суточные
        sutochnie_budget = people_count * days_командировки * daily_rate
        
        # Остаток бюджета делим между проездом и проживанием
        remaining_budget = children_budget - sutochnie_budget
        
        if remaining_budget > 0:
            # 50% на проезд, 50% на проживание
            proezd_budget = remaining_budget * 0.5
            prozhivanie_budget = remaining_budget * 0.5
        else:
            # Если суточные превышают весь бюджет, корректируем
            sutochnie_budget = children_budget * 0.4
            proezd_budget = children_budget * 0.3
            prozhivanie_budget = children_budget * 0.3
            # Пересчитываем дни командировки исходя из скорректированного бюджета
            days_командировки = int(sutochnie_budget / (people_count * daily_rate)) if people_count > 0 else 5
            if days_командировки < 1:
                days_командировки = 1
        
        # ПРОЕЗД
        # Обычно: количество детей * 2 стороны * ставка
        days_proezd = 2  # туда и обратно
        rate_proezd = EstimateGenerator.round_to_beautiful(proezd_budget / (people_count * days_proezd))
        
        db.add_estimate_item(
            estimate_id,
            'Проезд',
            description=f"маршрут: {event.location}",
            people_count=people_count,
            days_count=days_proezd,
            rate=rate_proezd
        )
        
        # ПРОЖИВАНИЕ
        # Количество дней = дни командировки
        rate_prozhivanie = EstimateGenerator.round_to_beautiful(prozhivanie_budget / (people_count * days_командировки))
        
        db.add_estimate_item(
            estimate_id,
            'Проживание',
            description="",
            people_count=people_count,
            days_count=days_командировки,
            rate=rate_prozhivanie
        )
        
        # СУТОЧНЫЕ
        # Используем фиксированную ставку в зависимости от региона
        db.add_estimate_item(
            estimate_id,
            'Суточные',
            description=f"по территории ({daily_rate} руб/день)",
            people_count=people_count,
            days_count=days_командировки,
            rate=daily_rate
        )
        
        return estimate_id
    
    @staticmethod
    def generate_trainer_estimates(db, event, trainers_budget, trainers_count):
        """
        Создать сметы на тренеров (УЭВП) по шаблону
        
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
            
            # Определяем ставку суточных в зависимости от региона
            daily_rate = EstimateGenerator.get_daily_rate(event.location)
            
            people_count = 1  # один тренер
            
            # Примерное количество дней командировки
            days_командировки = 5
            
            # Рассчитываем сумму на суточные (1 человек × дни × ставка)
            sutochnie_budget = people_count * days_командировки * daily_rate
            
            # Остаток бюджета делим между проездом и проживанием
            remaining_budget = budget_per_trainer - sutochnie_budget
            
            if remaining_budget > 0:
                # 50% на проезд, 50% на проживание
                proezd_budget = remaining_budget * 0.5
                prozhivanie_budget = remaining_budget * 0.5
            else:
                # Если суточные превышают весь бюджет, корректируем
                sutochnie_budget = budget_per_trainer * 0.35
                proezd_budget = budget_per_trainer * 0.35
                prozhivanie_budget = budget_per_trainer * 0.30
                # Пересчитываем дни командировки исходя из скорректированного бюджета
                days_командировки = int(sutochnie_budget / daily_rate) if daily_rate > 0 else 5
                if days_командировки < 1:
                    days_командировки = 1
            
            # ПРОЕЗД
            days_proezd = 2  # туда и обратно
            rate_proezd = EstimateGenerator.round_to_beautiful(proezd_budget / (people_count * days_proezd))
            
            db.add_estimate_item(
                estimate_id,
                'Проезд',
                description=f"маршрут: {event.location}",
                people_count=people_count,
                days_count=days_proezd,
                rate=rate_proezd
            )
            
            # ПРОЖИВАНИЕ
            # Количество дней = дни командировки
            rate_prozhivanie = EstimateGenerator.round_to_beautiful(prozhivanie_budget / (people_count * days_командировки))
            
            db.add_estimate_item(
                estimate_id,
                'Проживание',
                description="",
                people_count=people_count,
                days_count=days_командировки,
                rate=rate_prozhivanie
            )
            
            # СУТОЧНЫЕ
            # Используем фиксированную ставку в зависимости от региона (1 человек)
            db.add_estimate_item(
                estimate_id,
                'Суточные',
                description=f"по территории ({daily_rate} руб/день)",
                people_count=people_count,
                days_count=days_командировки,
                rate=daily_rate
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

