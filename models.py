# -*- coding: utf-8 -*-
"""
Модели данных приложения
"""

import json


class Event:
    """Класс модели мероприятия"""
    
    def __init__(self, event_id: int = None, year: int = None, sport: str = "", 
                 event_type: str = "", name: str = "", location: str = "", 
                 month: str = "", children_budget: float = 0.0, 
                 trainers_count: int = 1, trainers_budget: float = 0.0, 
                 notes: str = "", status: str = "Запланировано",
                 actual_start_date: str = None, actual_end_date: str = None,
                 actual_children_budget: float = None, actual_trainers_budget: float = None,
                 cancellation_reason: str = None, postponement_reason: str = None,
                 is_favorite: int = 0, last_modified: str = None, trainers_json: str = None,
                 actual_trainers_json: str = None):
        """
        Инициализация мероприятия
        
        Args:
            event_id: ID мероприятия
            year: Год
            sport: Вид спорта
            event_type: Тип мероприятия (Внутреннее/Выездное)
            name: Название мероприятия
            location: Место проведения
            month: Месяц
            children_budget: Заложенная сумма на детей
            trainers_count: Количество тренеров
            trainers_budget: Сумма на тренеров
            notes: Примечания
            status: Статус мероприятия
            actual_start_date: Фактическая дата начала
            actual_end_date: Фактическая дата окончания
            actual_children_budget: Фактически потраченная сумма на детей
            actual_trainers_budget: Фактически потраченная сумма на тренеров
            cancellation_reason: Причина отмены
            postponement_reason: Причина переноса
            is_favorite: Избранное (0/1)
            last_modified: Время последнего изменения
            trainers_json: JSON список тренеров
        """
        self.id = event_id
        self.year = year
        self.sport = sport
        self.event_type = event_type
        self.name = name
        self.location = location
        self.month = month
        self.children_budget = children_budget
        self.trainers_count = trainers_count
        self.trainers_budget = trainers_budget
        self.notes = notes
        self.status = status
        self.actual_start_date = actual_start_date
        self.actual_end_date = actual_end_date
        self.actual_children_budget = actual_children_budget
        self.actual_trainers_budget = actual_trainers_budget
        self.cancellation_reason = cancellation_reason
        self.postponement_reason = postponement_reason
        self.is_favorite = is_favorite
        self.last_modified = last_modified
        self.trainers_json = trainers_json
        self.actual_trainers_json = actual_trainers_json
        
        # Парсим JSON тренеров (план)
        self.trainers_list = []
        if trainers_json:
            try:
                self.trainers_list = json.loads(trainers_json)
            except:
                self.trainers_list = []
        
        # Парсим JSON тренеров (факт)
        self.actual_trainers_list = []
        if actual_trainers_json:
            try:
                self.actual_trainers_list = json.loads(actual_trainers_json)
            except:
                self.actual_trainers_list = []
    
    @classmethod
    def from_db_row(cls, row: tuple):
        """
        Создать объект Event из строки БД
        
        Args:
            row: Кортеж с данными из БД
            
        Returns:
            Объект Event
        """
        return cls(
            event_id=row[0],
            year=row[1],
            sport=row[2],
            event_type=row[3],
            name=row[4],
            location=row[5],
            month=row[6],
            children_budget=row[7],
            trainers_count=row[8],
            trainers_budget=row[9],
            notes=row[10] if len(row) > 10 else "",
            status=row[11] if len(row) > 11 else "Запланировано",
            actual_start_date=row[12] if len(row) > 12 else None,
            actual_end_date=row[13] if len(row) > 13 else None,
            actual_children_budget=row[14] if len(row) > 14 else None,
            actual_trainers_budget=row[15] if len(row) > 15 else None,
            cancellation_reason=row[16] if len(row) > 16 else None,
            postponement_reason=row[17] if len(row) > 17 else None,
            is_favorite=row[18] if len(row) > 18 else 0,
            last_modified=row[19] if len(row) > 19 else None,
            trainers_json=row[20] if len(row) > 20 else None,
            actual_trainers_json=row[21] if len(row) > 21 else None
        )
    
    def to_tuple(self):
        """
        Преобразовать объект в кортеж для БД (без ID)
        
        Returns:
            Кортеж с данными мероприятия
        """
        return (
            self.year, self.sport, self.event_type, self.name, 
            self.location, self.month, self.children_budget, 
            self.trainers_count, self.trainers_budget, self.notes
        )
    
    def __str__(self):
        """Строковое представление мероприятия"""
        return f"{self.name} ({self.sport}, {self.month} {self.year})"


class Estimate:
    """Класс модели сметы"""
    
    def __init__(self, estimate_id: int = None, event_id: int = None,
                 estimate_type: str = "", trainer_name: str = None,
                 approved_by: str = "", place: str = "", start_date: str = "",
                 end_date: str = "", created_date: str = None, total_amount: float = 0.0):
        """
        Инициализация сметы
        
        Args:
            estimate_id: ID сметы
            event_id: ID мероприятия
            estimate_type: Тип сметы ('ППО' или 'УЭВП')
            trainer_name: ФИО тренера (для смет УЭВП)
            approved_by: Кто утверждает
            place: Место проведения
            start_date: Дата начала
            end_date: Дата окончания
            created_date: Дата создания
            total_amount: Общая сумма сметы
        """
        self.id = estimate_id
        self.event_id = event_id
        self.estimate_type = estimate_type
        self.trainer_name = trainer_name
        self.approved_by = approved_by
        self.place = place
        self.start_date = start_date
        self.end_date = end_date
        self.created_date = created_date
        self.total_amount = total_amount
        self.items = []  # Список статей расходов
    
    @classmethod
    def from_db_row(cls, row: tuple):
        """
        Создать объект Estimate из строки БД
        
        Args:
            row: Кортеж с данными из БД
            
        Returns:
            Объект Estimate
        """
        return cls(
            estimate_id=row[0],
            event_id=row[1],
            estimate_type=row[2],
            trainer_name=row[3],
            approved_by=row[4],
            place=row[5],
            start_date=row[6],
            end_date=row[7],
            created_date=row[8],
            total_amount=row[9]
        )
    
    def __str__(self):
        """Строковое представление сметы"""
        if self.estimate_type == 'УЭВП' and self.trainer_name:
            return f"Смета УЭВП - {self.trainer_name}"
        return f"Смета {self.estimate_type}"


class EstimateItem:
    """Класс модели статьи расходов сметы"""
    
    def __init__(self, item_id: int = None, estimate_id: int = None,
                 category: str = "", description: str = "",
                 people_count: int = 0, days_count: int = 0,
                 rate: float = 0.0, total: float = 0.0):
        """
        Инициализация статьи расходов
        
        Args:
            item_id: ID статьи расходов
            estimate_id: ID сметы
            category: Категория (Проезд, Проживание, Суточные, Питание)
            description: Описание/маршрут
            people_count: Количество человек
            days_count: Количество дней
            rate: Ставка
            total: Итоговая сумма
        """
        self.id = item_id
        self.estimate_id = estimate_id
        self.category = category
        self.description = description
        self.people_count = people_count
        self.days_count = days_count
        self.rate = rate
        self.total = total
    
    @classmethod
    def from_db_row(cls, row: tuple):
        """
        Создать объект EstimateItem из строки БД
        
        Args:
            row: Кортеж с данными из БД
            
        Returns:
            Объект EstimateItem
        """
        return cls(
            item_id=row[0],
            estimate_id=row[1],
            category=row[2],
            description=row[3],
            people_count=row[4],
            days_count=row[5],
            rate=row[6],
            total=row[7]
        )
    
    def __str__(self):
        """Строковое представление статьи расходов"""
        return f"{self.category}: {self.total:.2f} руб."
