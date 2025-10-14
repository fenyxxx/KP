# -*- coding: utf-8 -*-
"""
Генератор смет по шаблонам для выездных мероприятий
"""

import math


class EstimateGenerator:
    """Класс для автоматической генерации смет по шаблонам"""
    
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
        
        # Распределение бюджета по шаблону:
        # 30% - Проезд
        # 30% - Проживание  
        # 40% - Суточные или Питание
        
        proezd_budget = children_budget * 0.3
        prozhivanie_budget = children_budget * 0.3
        sutochnie_budget = children_budget * 0.4
        
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
        # Обычно: 3-5 дней
        days_prozhivanie = 4
        rate_prozhivanie = EstimateGenerator.round_to_beautiful(prozhivanie_budget / (people_count * days_prozhivanie))
        
        db.add_estimate_item(
            estimate_id,
            'Проживание',
            description="",
            people_count=people_count,
            days_count=days_prozhivanie,
            rate=rate_prozhivanie
        )
        
        # СУТОЧНЫЕ
        days_sutochnie = 5
        rate_sutochnie = EstimateGenerator.round_to_beautiful(sutochnie_budget / (people_count * days_sutochnie))
        
        db.add_estimate_item(
            estimate_id,
            'Суточные',
            description="",
            people_count=people_count,
            days_count=days_sutochnie,
            rate=rate_sutochnie
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
            
            # Распределение бюджета по шаблону для тренера:
            # 35% - Проезд
            # 35% - Проживание
            # 30% - Суточные
            
            proezd_budget = budget_per_trainer * 0.35
            prozhivanie_budget = budget_per_trainer * 0.35
            sutochnie_budget = budget_per_trainer * 0.30
            
            people_count = 1  # один тренер
            
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
            days_prozhivanie = 5
            rate_prozhivanie = EstimateGenerator.round_to_beautiful(prozhivanie_budget / (people_count * days_prozhivanie))
            
            db.add_estimate_item(
                estimate_id,
                'Проживание',
                description="",
                people_count=people_count,
                days_count=days_prozhivanie,
                rate=rate_prozhivanie
            )
            
            # СУТОЧНЫЕ
            days_sutochnie = 5
            rate_sutochnie = EstimateGenerator.round_to_beautiful(sutochnie_budget / (people_count * days_sutochnie))
            
            db.add_estimate_item(
                estimate_id,
                'Суточные',
                description="",
                people_count=people_count,
                days_count=days_sutochnie,
                rate=rate_sutochnie
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

