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

