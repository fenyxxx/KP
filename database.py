# -*- coding: utf-8 -*-
"""
Класс для работы с базой данных SQLite
"""

import sqlite3
from typing import List, Optional
import os
import json
from datetime import datetime


class Database:
    """Класс для работы с базой данных календарных планов"""
    
    def __init__(self, db_name: str = "calendar_plans.db"):
        """
        Инициализация подключения к БД
        
        Args:
            db_name: Имя файла базы данных
        """
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Установить соединение с БД"""
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
    
    def _create_tables(self):
        """Создать необходимые таблицы"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                sport TEXT NOT NULL,
                event_type TEXT NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                month TEXT NOT NULL,
                children_budget REAL NOT NULL,
                trainers_count INTEGER DEFAULT 1,
                trainers_budget REAL NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'Запланировано',
                actual_start_date TEXT,
                actual_end_date TEXT,
                actual_children_budget REAL,
                actual_trainers_budget REAL,
                cancellation_reason TEXT,
                postponement_reason TEXT
            )
        ''')
        self.connection.commit()
        
        # Добавляем новые столбцы если таблица уже существует
        self._add_columns_if_not_exist()
    
    def _add_columns_if_not_exist(self):
        """Добавить новые столбцы в существующую таблицу"""
        columns_to_add = [
            ("status", "TEXT DEFAULT 'Запланировано'"),
            ("actual_start_date", "TEXT"),
            ("actual_end_date", "TEXT"),
            ("actual_children_budget", "REAL"),
            ("actual_trainers_budget", "REAL"),
            ("cancellation_reason", "TEXT"),
            ("postponement_reason", "TEXT"),
            ("is_favorite", "INTEGER DEFAULT 0"),
            ("last_modified", "TEXT"),
            ("trainers_json", "TEXT"),
            ("actual_trainers_json", "TEXT")  # Фактические данные по тренерам
        ]
        
        # Получаем список существующих столбцов
        self.cursor.execute("PRAGMA table_info(events)")
        existing_columns = [row[1] for row in self.cursor.fetchall()]
        
        # Добавляем отсутствующие столбцы
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    self.cursor.execute(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}")
                    self.connection.commit()
                except Exception:
                    pass  # Столбец уже существует
        
        # Миграция данных тренеров в JSON формат
        self._migrate_trainers_to_json()
    
    def _migrate_trainers_to_json(self):
        """Миграция старых данных тренеров в JSON формат"""
        try:
            # Проверяем, есть ли записи без trainers_json
            self.cursor.execute('''
                SELECT id, trainers_count, trainers_budget 
                FROM events 
                WHERE trainers_json IS NULL OR trainers_json = ""
            ''')
            rows = self.cursor.fetchall()
            
            for event_id, count, budget in rows:
                # Создаём JSON с тренерами
                trainers = []
                if count and count > 0:
                    budget_per_trainer = budget / count if budget else 0
                    for i in range(count):
                        trainers.append({
                            "name": f"Тренер {i+1}",
                            "budget": budget_per_trainer
                        })
                
                trainers_json = json.dumps(trainers, ensure_ascii=False)
                self.cursor.execute('''
                    UPDATE events 
                    SET trainers_json = ?,
                        last_modified = ?
                    WHERE id = ?
                ''', (trainers_json, datetime.now().isoformat(), event_id))
            
            self.connection.commit()
        except Exception as e:
            pass  # Таблица может быть пустая или миграция уже выполнена
    
    def add_event(self, year: int, sport: str, event_type: str, name: str, 
                  location: str, month: str, children_budget: float, 
                  trainers_list: list = None, notes: str = "",
                  # Старые параметры для обратной совместимости
                  trainers_count: int = None, trainers_budget: float = None) -> int:
        """
        Добавить мероприятие в БД
        
        Args:
            trainers_list: Список словарей с тренерами [{"name": "...", "budget": ...}, ...]
        
        Returns:
            ID созданного мероприятия
        """
        # Обратная совместимость: если передан старый формат, конвертируем
        if trainers_list is None:
            trainers_list = []
            if trainers_count and trainers_count > 0:
                budget_per_trainer = (trainers_budget or 0) / trainers_count
                for i in range(trainers_count):
                    trainers_list.append({
                        "name": f"Тренер {i+1}",
                        "budget": budget_per_trainer
                    })
        
        trainers_json = json.dumps(trainers_list, ensure_ascii=False)
        total_trainers_budget = sum(t.get('budget', 0) for t in trainers_list)
        
        self.cursor.execute('''
            INSERT INTO events (year, sport, event_type, name, location, month, 
                              children_budget, trainers_count, trainers_budget, notes,
                              trainers_json, last_modified, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (year, sport, event_type, name, location, month, children_budget, 
              len(trainers_list), total_trainers_budget, notes, trainers_json,
              datetime.now().isoformat()))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_events_by_year(self, year: int) -> List[tuple]:
        """
        Получить все мероприятия за указанный год
        
        Returns:
            Список кортежей с данными мероприятий
        """
        self.cursor.execute('''
            SELECT id, year, sport, event_type, name, location, month, 
                   children_budget, trainers_count, trainers_budget, notes,
                   status, actual_start_date, actual_end_date, 
                   actual_children_budget, actual_trainers_budget,
                   cancellation_reason, postponement_reason,
                   is_favorite, last_modified, trainers_json, actual_trainers_json
            FROM events
            WHERE year = ?
            ORDER BY 
                CASE month
                    WHEN 'Январь' THEN 1
                    WHEN 'Февраль' THEN 2
                    WHEN 'Март' THEN 3
                    WHEN 'Апрель' THEN 4
                    WHEN 'Май' THEN 5
                    WHEN 'Июнь' THEN 6
                    WHEN 'Июль' THEN 7
                    WHEN 'Август' THEN 8
                    WHEN 'Сентябрь' THEN 9
                    WHEN 'Октябрь' THEN 10
                    WHEN 'Ноябрь' THEN 11
                    WHEN 'Декабрь' THEN 12
                END,
                event_type,
                id
        ''', (year,))
        return self.cursor.fetchall()
    
    def get_event_by_id(self, event_id: int) -> Optional[tuple]:
        """Получить мероприятие по ID"""
        self.cursor.execute('''
            SELECT id, year, sport, event_type, name, location, month, 
                   children_budget, trainers_count, trainers_budget, notes,
                   status, actual_start_date, actual_end_date, 
                   actual_children_budget, actual_trainers_budget,
                   cancellation_reason, postponement_reason,
                   is_favorite, last_modified, trainers_json, actual_trainers_json
            FROM events
            WHERE id = ?
        ''', (event_id,))
        return self.cursor.fetchone()
    
    def update_event(self, event_id: int, year: int, sport: str, event_type: str, 
                    name: str, location: str, month: str, children_budget: float, 
                    trainers_list: list = None, notes: str = "",
                    # Старые параметры для обратной совместимости
                    trainers_count: int = None, trainers_budget: float = None):
        """Обновить мероприятие"""
        # Обратная совместимость
        if trainers_list is None:
            trainers_list = []
            if trainers_count and trainers_count > 0:
                budget_per_trainer = (trainers_budget or 0) / trainers_count
                for i in range(trainers_count):
                    trainers_list.append({
                        "name": f"Тренер {i+1}",
                        "budget": budget_per_trainer
                    })
        
        trainers_json = json.dumps(trainers_list, ensure_ascii=False)
        total_trainers_budget = sum(t.get('budget', 0) for t in trainers_list)
        
        self.cursor.execute('''
            UPDATE events
            SET year = ?, sport = ?, event_type = ?, name = ?, location = ?, 
                month = ?, children_budget = ?, trainers_count = ?, 
                trainers_budget = ?, notes = ?, trainers_json = ?, last_modified = ?
            WHERE id = ?
        ''', (year, sport, event_type, name, location, month, children_budget, 
              len(trainers_list), total_trainers_budget, notes, trainers_json,
              datetime.now().isoformat(), event_id))
        self.connection.commit()
    
    def update_event_clarification(self, event_id: int, status: str, 
                                   actual_start_date: str = None, actual_end_date: str = None,
                                   actual_children_budget: float = None, 
                                   actual_trainers_budget: float = None,
                                   cancellation_reason: str = None, 
                                   postponement_reason: str = None,
                                   actual_trainers_list: list = None):
        """Обновить уточнения мероприятия"""
        actual_trainers_json = None
        if actual_trainers_list:
            actual_trainers_json = json.dumps(actual_trainers_list, ensure_ascii=False)
        
        self.cursor.execute('''
            UPDATE events
            SET status = ?, actual_start_date = ?, actual_end_date = ?,
                actual_children_budget = ?, actual_trainers_budget = ?,
                cancellation_reason = ?, postponement_reason = ?,
                actual_trainers_json = ?, last_modified = ?
            WHERE id = ?
        ''', (status, actual_start_date, actual_end_date, actual_children_budget,
              actual_trainers_budget, cancellation_reason, postponement_reason,
              actual_trainers_json, datetime.now().isoformat(), event_id))
        self.connection.commit()
    
    def delete_event(self, event_id: int):
        """Удалить мероприятие"""
        self.cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        self.connection.commit()
    
    def get_all_years(self) -> List[int]:
        """Получить список всех годов в БД"""
        self.cursor.execute('SELECT DISTINCT year FROM events ORDER BY year')
        return [row[0] for row in self.cursor.fetchall()]
    
    def toggle_favorite(self, event_id: int):
        """Переключить статус избранного для мероприятия"""
        self.cursor.execute('''
            UPDATE events 
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END,
                last_modified = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), event_id))
        self.connection.commit()
    
    def get_favorite_events(self, year: int) -> List[tuple]:
        """Получить избранные мероприятия за год"""
        self.cursor.execute('''
            SELECT id, year, sport, event_type, name, location, month, 
                   children_budget, trainers_count, trainers_budget, notes,
                   status, actual_start_date, actual_end_date, 
                   actual_children_budget, actual_trainers_budget,
                   cancellation_reason, postponement_reason,
                   is_favorite, last_modified, trainers_json, actual_trainers_json
            FROM events
            WHERE year = ? AND is_favorite = 1
            ORDER BY 
                CASE month
                    WHEN 'Январь' THEN 1
                    WHEN 'Февраль' THEN 2
                    WHEN 'Март' THEN 3
                    WHEN 'Апрель' THEN 4
                    WHEN 'Май' THEN 5
                    WHEN 'Июнь' THEN 6
                    WHEN 'Июль' THEN 7
                    WHEN 'Август' THEN 8
                    WHEN 'Сентябрь' THEN 9
                    WHEN 'Октябрь' THEN 10
                    WHEN 'Ноябрь' THEN 11
                    WHEN 'Декабрь' THEN 12
                END,
                event_type,
                id
        ''', (year,))
        return self.cursor.fetchall()
    
    def close(self):
        """Закрыть соединение с БД"""
        if self.connection:
            self.connection.close()

