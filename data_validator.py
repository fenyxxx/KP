# -*- coding: utf-8 -*-
"""
Модуль для проверки целостности данных
"""

from typing import List, Dict
from models import Event


class DataValidator:
    """Класс для проверки целостности данных мероприятий"""
    
    def __init__(self, db):
        """
        Инициализация валидатора
        
        Args:
            db: Объект базы данных
        """
        self.db = db
    
    def check_all(self, year: int) -> Dict[str, List[Dict]]:
        """
        Выполнить все проверки для указанного года
        
        Args:
            year: Год для проверки
            
        Returns:
            Словарь с результатами проверок
        """
        results = {
            'no_budget': [],
            'no_actual_dates': [],
            'no_cancellation_reason': [],
            'zero_total_budget': [],
            'suspicious_budget': [],
            'no_trainers': []
        }
        
        events_data = self.db.get_events_by_year(year)
        
        for row in events_data:
            event = Event.from_db_row(row)
            
            # Проверка 1: Мероприятия без бюджета
            if event.children_budget == 0 and event.trainers_budget == 0:
                results['zero_total_budget'].append({
                    'id': event.id,
                    'name': event.name,
                    'month': event.month,
                    'issue': 'Нет бюджета ни на детей, ни на тренеров'
                })
            
            # Проверка 2: Проведённые без фактических дат
            if event.status == "Проведено":
                if not event.actual_start_date or not event.actual_end_date:
                    results['no_actual_dates'].append({
                        'id': event.id,
                        'name': event.name,
                        'month': event.month,
                        'issue': 'Мероприятие проведено, но нет фактических дат'
                    })
            
            # Проверка 3: Отменённые без причины
            if event.status == "Отменено":
                if not event.cancellation_reason:
                    results['no_cancellation_reason'].append({
                        'id': event.id,
                        'name': event.name,
                        'month': event.month,
                        'issue': 'Мероприятие отменено, но не указана причина'
                    })
            
            # Проверка 4: Подозрительные фактические расходы (> план * 2)
            if event.status == "Проведено":
                if event.actual_children_budget and event.children_budget > 0:
                    if event.actual_children_budget > event.children_budget * 2:
                        results['suspicious_budget'].append({
                            'id': event.id,
                            'name': event.name,
                            'month': event.month,
                            'issue': f'Фактические расходы на детей ({event.actual_children_budget:.2f} ₽) ' +
                                   f'превышают план в 2+ раза ({event.children_budget:.2f} ₽)'
                        })
                
                if event.actual_trainers_budget and event.trainers_budget > 0:
                    if event.actual_trainers_budget > event.trainers_budget * 2:
                        results['suspicious_budget'].append({
                            'id': event.id,
                            'name': event.name,
                            'month': event.month,
                            'issue': f'Фактические расходы на тренеров ({event.actual_trainers_budget:.2f} ₽) ' +
                                   f'превышают план в 2+ раза ({event.trainers_budget:.2f} ₽)'
                        })
            
            # Проверка 5: Выездные мероприятия без тренеров
            if event.event_type == "Выездное":
                if not event.trainers_list and event.trainers_budget == 0:
                    results['no_trainers'].append({
                        'id': event.id,
                        'name': event.name,
                        'month': event.month,
                        'issue': 'Выездное мероприятие без тренеров и бюджета на них'
                    })
        
        return results
    
    def get_summary(self, results: Dict[str, List[Dict]]) -> str:
        """
        Получить текстовое резюме проверки
        
        Args:
            results: Результаты проверок
            
        Returns:
            Текстовое резюме
        """
        total_issues = sum(len(issues) for issues in results.values())
        
        if total_issues == 0:
            return "✅ Проблем не обнаружено! Все данные корректны."
        
        summary = f"⚠️ Найдено проблем: {total_issues}\n\n"
        
        if results['zero_total_budget']:
            summary += f"❌ Без бюджета: {len(results['zero_total_budget'])}\n"
        
        if results['no_actual_dates']:
            summary += f"📅 Проведённые без дат: {len(results['no_actual_dates'])}\n"
        
        if results['no_cancellation_reason']:
            summary += f"📝 Отменённые без причины: {len(results['no_cancellation_reason'])}\n"
        
        if results['suspicious_budget']:
            summary += f"💰 Подозрительные расходы: {len(results['suspicious_budget'])}\n"
        
        if results['no_trainers']:
            summary += f"👨‍🏫 Выездные без тренеров: {len(results['no_trainers'])}\n"
        
        return summary

