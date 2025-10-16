# -*- coding: utf-8 -*-
"""
Окно для просмотра календарного плана
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from constants import MONTHS
from models import Event
from styles import MONOSPACE_FONT
import csv
import html
import webbrowser
import os


def format_rubles(amount):
    """
    Форматировать сумму в российском стиле с разделителями
    
    Args:
        amount: Сумма в рублях
        
    Returns:
        Отформатированная строка (например: "1 234 567 руб.")
    """
    if amount is None or amount == 0:
        return "0 руб."
    
    # Округляем до рублей
    amount = int(round(amount))
    
    # Форматируем с пробелами как разделителями тысяч
    formatted = "{:,}".format(amount).replace(',', ' ')
    
    return f"{formatted} руб."


def format_number_ru(number, decimals=2):
    """
    Форматировать число для Excel (русская локаль) - с запятой вместо точки
    
    Args:
        number: Число для форматирования
        decimals: Количество знаков после запятой (по умолчанию 2)
        
    Returns:
        Строка с числом, где десятичный разделитель - запятая
    """
    if number is None:
        return ""
    if number == 0 or number == 0.0:
        return "0"
    
    # Форматируем число с нужным количеством знаков после точки
    formatted = f"{number:.{decimals}f}"
    
    # Заменяем точку на запятую для Excel
    formatted = formatted.replace('.', ',')
    
    return formatted


def format_number(amount):
    """
    Форматировать число с разделителями тысяч (без валюты)
    
    Args:
        amount: Число
        
    Returns:
        Отформатированная строка (например: "1 234 567")
    """
    if amount is None or amount == 0:
        return "0"
    
    # Округляем до целого
    amount = int(round(amount))
    
    # Форматируем с пробелами как разделителями тысяч
    formatted = "{:,}".format(amount).replace(',', ' ')
    
    return formatted


class ViewPlanWindow:
    """Класс окна для просмотра календарного плана"""
    
    def __init__(self, parent, db, year: int, initial_report_type: str = 'full'):
        """
        Инициализация окна
        
        Args:
            parent: Родительское окно
            db: Объект базы данных
            year: Год для отображения
            initial_report_type: Начальный тип отчёта для отображения
        """
        self.parent = parent
        self.db = db
        self.year = year
        self.current_report_type = initial_report_type  # Текущий тип отчёта
        
        # Создаем окно
        self.window = tk.Toplevel(parent)
        self.window.title(f"Календарный план {year}")
        
        # Разворачиваем окно на весь экран (кроссплатформенно)
        try:
            # Пробуем Windows-способ
            self.window.state('zoomed')
        except:
            # Для Linux (Red OS) - разворачиваем через geometry
            try:
                # Получаем размер экрана
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
                self.window.geometry(f"{screen_width}x{screen_height}+0+0")
            except:
                # Если и это не работает, устанавливаем большой размер
                self.window.geometry("1400x900")
        
        # Центрируем окно
        self.window.transient(parent)
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._create_widgets()
        self._show_report(initial_report_type)  # Показываем указанный тип отчёта
    
    def _create_widgets(self):
        """Создать виджеты окна"""
        # Заголовок
        header = ttk.Label(
            self.window, 
            text=f"Календарный план на {self.year} год",
            font=('Arial', 14, 'bold')
        )
        header.pack(pady=10)
        
        # Панель с кнопками отчётов
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(button_frame, text="Тип отчёта:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="Полный календарный план", 
            command=lambda: self._show_report('full')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="Финансовый отчёт", 
            command=lambda: self._show_report('financial')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="По видам спорта", 
            command=lambda: self._show_report('sports')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="По статусам", 
            command=lambda: self._show_report('status')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="Краткая сводка", 
            command=lambda: self._show_report('summary')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="По типам мероприятий", 
            command=lambda: self._show_report('by_type')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="📊 Годовой отчет ППО", 
            command=lambda: self._show_report('annual_ppo'),
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, text="📋 Годовой отчет УЭВП", 
            command=lambda: self._show_report('annual_uevp'),
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
        # Панель с кнопками сохранения
        save_frame = ttk.Frame(self.window)
        save_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        ttk.Label(save_frame, text="💾 Сохранить:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            save_frame, text="TXT", 
            command=lambda: self._save_report('txt')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            save_frame, text="CSV", 
            command=lambda: self._save_report('csv')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            save_frame, text="HTML", 
            command=lambda: self._save_report('html')
        ).pack(side=tk.LEFT, padx=2)
        
        # Текстовое поле с прокруткой
        self.text_area = scrolledtext.ScrolledText(
            self.window, 
            wrap=tk.WORD, 
            width=100, 
            height=35,
            font=(MONOSPACE_FONT, 10)
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Кнопка закрытия
        ttk.Button(
            self.window, 
            text="Закрыть", 
            command=self.window.destroy
        ).pack(pady=10)
    
    def _show_report(self, report_type):
        """Показать выбранный тип отчёта"""
        self.current_report_type = report_type  # Сохраняем текущий тип
        
        # Обновляем заголовок окна
        report_titles = {
            'full': 'Полный календарный план',
            'financial': 'Финансовый отчёт',
            'sports': 'Отчёт по видам спорта',
            'status': 'Отчёт по статусам',
            'summary': 'Краткая сводка',
            'by_type': 'Финансовый отчёт по типам мероприятий',
            'annual_ppo': 'Годовой отчет ППО',
            'annual_uevp': 'Годовой отчет УЭВП - Потребность на командировочные расходы'
        }
        title = report_titles.get(report_type, 'Календарный план')
        self.window.title(f"{title} - {self.year}")
        
        # Очищаем текстовое поле
        self.text_area.config(state='normal')
        self.text_area.delete('1.0', tk.END)
        
        if report_type == 'full':
            self._load_full_plan()
        elif report_type == 'financial':
            self._load_financial_report()
        elif report_type == 'sports':
            self._load_sports_report()
        elif report_type == 'status':
            self._load_status_report()
        elif report_type == 'summary':
            self._load_summary_report()
        elif report_type == 'by_type':
            self._load_by_type_report()
        elif report_type == 'annual_ppo':
            self._load_annual_ppo_report()
        elif report_type == 'annual_uevp':
            self._load_annual_uevp_report()
        
        self.text_area.config(state='disabled')
    
    def _load_full_plan(self):
        """Загрузить полный календарный план"""
        # Получаем все мероприятия за год
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        # Преобразуем в объекты Event
        events = [Event.from_db_row(row) for row in events_data]
        
        # Группируем по месяцам
        events_by_month = {}
        for event in events:
            if event.month not in events_by_month:
                events_by_month[event.month] = []
            events_by_month[event.month].append(event)
        
        # Формируем текст плана
        plan_text = ""
        plan_text += "=" * 90 + "\n"
        plan_text += f"КАЛЕНДАРНЫЙ ПЛАН НА {self.year} ГОД\n"
        plan_text += "=" * 90 + "\n\n"
        
        # Итоговые суммы
        total_children_budget = 0
        total_trainers_budget = 0
        total_events = len(events)
        
        # Проходим по месяцам в правильном порядке
        for month in MONTHS:
            if month not in events_by_month:
                continue
            
            month_events = events_by_month[month]
            
            # Разделяем на внутренние и выездные
            internal_events = [e for e in month_events if e.event_type == "Внутреннее"]
            external_events = [e for e in month_events if e.event_type == "Выездное"]
            
            plan_text += "-" * 90 + "\n"
            plan_text += f"{month.upper()}\n"
            plan_text += "-" * 90 + "\n\n"
            
            # Внутренние мероприятия
            if internal_events:
                plan_text += "ВНУТРЕННИЕ МЕРОПРИЯТИЯ:\n\n"
                for i, event in enumerate(internal_events, 1):
                    plan_text += f"{i}. {event.sport}"
                    
                    # Статус мероприятия
                    if event.status and event.status != "Запланировано":
                        plan_text += f" [{event.status.upper()}]"
                    plan_text += "\n"
                    
                    plan_text += f"   Название: {event.name}\n"
                    plan_text += f"   Место: {event.location}\n"
                    
                    # Даты проведения
                    if event.actual_start_date or event.actual_end_date:
                        dates = []
                        if event.actual_start_date:
                            dates.append(event.actual_start_date)
                        if event.actual_end_date and event.actual_end_date != event.actual_start_date:
                            dates.append(event.actual_end_date)
                        plan_text += f"   Даты проведения: {' - '.join(dates)}\n"
                    
                    # Бюджет
                    plan_text += f"   Сумма на детей: {format_rubles(event.children_budget)}"
                    if event.actual_children_budget is not None:
                        plan_text += f" (факт: {format_rubles(event.actual_children_budget)})"
                    plan_text += "\n"
                    
                    # Информация о тренерах
                    if event.trainers_list:
                        total_budget = sum(t.get('budget', 0) for t in event.trainers_list)
                        plan_text += f"   Тренеры ({len(event.trainers_list)} чел.): {format_rubles(total_budget)}"
                        if event.actual_trainers_budget is not None:
                            plan_text += f" (факт: {format_rubles(event.actual_trainers_budget)})"
                        plan_text += "\n"
                        for i, trainer in enumerate(event.trainers_list, 1):
                            plan_text += f"     {i}. {trainer.get('name', 'Без имени')} - {format_rubles(trainer.get('budget', 0))}\n"
                    else:
                        plan_text += f"   Тренеров: {event.trainers_count}, сумма: {format_rubles(event.trainers_budget)}"
                        if event.actual_trainers_budget is not None:
                            plan_text += f" (факт: {format_rubles(event.actual_trainers_budget)})"
                        plan_text += "\n"
                    
                    # Причины отмены/переноса
                    if event.status == "Отменено" and event.cancellation_reason:
                        plan_text += f"   Причина отмены: {event.cancellation_reason}\n"
                    elif event.status == "Перенесено" and event.postponement_reason:
                        plan_text += f"   Причина переноса: {event.postponement_reason}\n"
                    
                    if event.notes:
                        plan_text += f"   Примечания: {event.notes}\n"
                    plan_text += "\n"
            
            # Выездные мероприятия
            if external_events:
                plan_text += "ВЫЕЗДНЫЕ МЕРОПРИЯТИЯ:\n\n"
                for i, event in enumerate(external_events, 1):
                    plan_text += f"{i}. {event.sport}"
                    
                    # Статус мероприятия
                    if event.status and event.status != "Запланировано":
                        plan_text += f" [{event.status.upper()}]"
                    plan_text += "\n"
                    
                    plan_text += f"   Название: {event.name}\n"
                    plan_text += f"   Место: {event.location}\n"
                    
                    # Даты проведения
                    if event.actual_start_date or event.actual_end_date:
                        dates = []
                        if event.actual_start_date:
                            dates.append(event.actual_start_date)
                        if event.actual_end_date and event.actual_end_date != event.actual_start_date:
                            dates.append(event.actual_end_date)
                        plan_text += f"   Даты проведения: {' - '.join(dates)}\n"
                    
                    # Бюджет
                    plan_text += f"   Сумма на детей: {format_rubles(event.children_budget)}"
                    if event.actual_children_budget is not None:
                        plan_text += f" (факт: {format_rubles(event.actual_children_budget)})"
                    plan_text += "\n"
                    
                    # Информация о тренерах
                    if event.trainers_list:
                        total_budget = sum(t.get('budget', 0) for t in event.trainers_list)
                        plan_text += f"   Тренеры ({len(event.trainers_list)} чел.): {format_rubles(total_budget)}"
                        if event.actual_trainers_budget is not None:
                            plan_text += f" (факт: {format_rubles(event.actual_trainers_budget)})"
                        plan_text += "\n"
                        for i, trainer in enumerate(event.trainers_list, 1):
                            plan_text += f"     {i}. {trainer.get('name', 'Без имени')} - {format_rubles(trainer.get('budget', 0))}\n"
                    else:
                        plan_text += f"   Тренеров: {event.trainers_count}, сумма: {format_rubles(event.trainers_budget)}"
                        if event.actual_trainers_budget is not None:
                            plan_text += f" (факт: {format_rubles(event.actual_trainers_budget)})"
                        plan_text += "\n"
                    
                    # Причины отмены/переноса
                    if event.status == "Отменено" and event.cancellation_reason:
                        plan_text += f"   Причина отмены: {event.cancellation_reason}\n"
                    elif event.status == "Перенесено" and event.postponement_reason:
                        plan_text += f"   Причина переноса: {event.postponement_reason}\n"
                    
                    if event.notes:
                        plan_text += f"   Примечания: {event.notes}\n"
                    plan_text += "\n"
            
            plan_text += "\n"
        
        # Итоги - детальная статистика
        plan_text += "=" * 90 + "\n"
        plan_text += "ИТОГОВАЯ СТАТИСТИКА\n"
        plan_text += "=" * 90 + "\n"
        
        # Общая информация
        plan_text += f"Всего мероприятий: {total_events}\n"
        
        # Подсчет по статусам
        status_counts = {}
        for event in events:
            status = event.status or "Запланировано"
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            plan_text += "\nПо статусам:\n"
            for status, count in sorted(status_counts.items()):
                plan_text += f"  {status}: {count}\n"
        
        plan_text += "\n" + "-" * 90 + "\n"
        
        # Статистика по видам спорта
        plan_text += "\nСТАТИСТИКА ПО ВИДАМ СПОРТА:\n"
        plan_text += "-" * 90 + "\n"
        
        sport_stats = {}
        for event in events:
            if event.sport not in sport_stats:
                sport_stats[event.sport] = {
                    'count': 0,
                    'plan_children': 0,
                    'fact_children': 0,
                    'plan_trainers': 0,
                    'fact_trainers': 0,
                    'plan_children_completed': 0,  # План только для проведённых/отменённых
                    'plan_trainers_completed': 0   # План только для проведённых/отменённых
                }
            
            sport_stats[event.sport]['count'] += 1
            sport_stats[event.sport]['plan_children'] += event.children_budget
            sport_stats[event.sport]['plan_trainers'] += event.trainers_budget
            
            # Факт и план для проведённых/отменённых (для расчёта экономии/перерасхода)
            if event.status in ["Проведено", "Отменено"]:
                sport_stats[event.sport]['plan_children_completed'] += event.children_budget
                sport_stats[event.sport]['plan_trainers_completed'] += event.trainers_budget
                
                if event.status == "Проведено":
                    if event.actual_children_budget is not None:
                        sport_stats[event.sport]['fact_children'] += event.actual_children_budget
                    else:
                        # Если мероприятие проведено, но факт не указан - берём план
                        sport_stats[event.sport]['fact_children'] += event.children_budget
                    
                    if event.actual_trainers_budget is not None:
                        sport_stats[event.sport]['fact_trainers'] += event.actual_trainers_budget
                    else:
                        # Если мероприятие проведено, но факт не указан - берём план
                        sport_stats[event.sport]['fact_trainers'] += event.trainers_budget
                # Для отменённых факт = 0 (не тратили)
            # Для запланированных, перенесённых - факт = 0
        
        for sport in sorted(sport_stats.keys()):
            stats = sport_stats[sport]
            plan_text += f"\n{sport}:\n"
            plan_text += f"  Мероприятий: {stats['count']}\n"
            plan_text += f"  Бюджет детей:    план {format_number(stats['plan_children'])} → факт {format_number(stats['fact_children'])}"
            
            # Экономия/Перерасход считается только для проведённых/отменённых
            if stats['plan_children_completed'] > 0:
                diff_children = stats['plan_children_completed'] - stats['fact_children']
                if diff_children > 0:
                    plan_text += f" (экономия: {format_number(diff_children)})\n"
                elif diff_children < 0:
                    plan_text += f" (перерасход: {format_number(abs(diff_children))})\n"
                else:
                    plan_text += " (по плану)\n"
            else:
                plan_text += " (н/д)\n"
            
            plan_text += f"  Бюджет тренеров: план {format_number(stats['plan_trainers'])} → факт {format_number(stats['fact_trainers'])}"
            
            # Экономия/Перерасход считается только для проведённых/отменённых
            if stats['plan_trainers_completed'] > 0:
                diff_trainers = stats['plan_trainers_completed'] - stats['fact_trainers']
                if diff_trainers > 0:
                    plan_text += f" (экономия: {format_number(diff_trainers)})\n"
                elif diff_trainers < 0:
                    plan_text += f" (перерасход: {format_number(abs(diff_trainers))})\n"
                else:
                    plan_text += " (по плану)\n"
            else:
                plan_text += " (н/д)\n"
        
        plan_text += "\n" + "=" * 90 + "\n"
        
        # Итоги по бюджетам (раздельно по источникам финансирования)
        plan_text += "\nИТОГИ ПО БЮДЖЕТАМ:\n"
        plan_text += "=" * 90 + "\n"
        
        # Считаем плановые и фактические суммы
        # План включает ВСЕ мероприятия (даже отменённые - они были запланированы)
        plan_children_total = sum(e.children_budget for e in events)
        plan_trainers_total = sum(e.trainers_budget for e in events)
        
        # План для проведённых/отменённых (для расчёта экономии/перерасхода)
        plan_children_completed = sum(e.children_budget for e in events if e.status in ["Проведено", "Отменено"])
        plan_trainers_completed = sum(e.trainers_budget for e in events if e.status in ["Проведено", "Отменено"])
        
        # Факт только для проведённых мероприятий
        fact_children_total = sum(
            e.actual_children_budget if e.actual_children_budget is not None else e.children_budget
            for e in events if e.status == "Проведено"
        )
        fact_trainers_total = sum(
            e.actual_trainers_budget if e.actual_trainers_budget is not None else e.trainers_budget
            for e in events if e.status == "Проведено"
        )
        
        # Бюджет на детей (Профсоюз)
        plan_text += "\n1. БЮДЖЕТ НА ДЕТЕЙ\n"
        plan_text += "   Источник финансирования: ППО \"Газпром добыча Ямбург профсоюз\"\n"
        plan_text += "-" * 90 + "\n"
        plan_text += f"  Планируемые расходы: {format_rubles(plan_children_total)}\n"
        plan_text += f"  Фактические расходы: {format_rubles(fact_children_total)}\n"
        
        # Экономия/Перерасход только для проведённых/отменённых
        if plan_children_completed > 0:
            diff_children_total = plan_children_completed - fact_children_total
            if diff_children_total > 0:
                plan_text += f"  ✓ ЭКОНОМИЯ: {format_rubles(diff_children_total)} ({(diff_children_total/plan_children_completed*100):.1f}%)\n"
            elif diff_children_total < 0:
                plan_text += f"  ⚠ ПЕРЕРАСХОД: {format_rubles(abs(diff_children_total))} ({(abs(diff_children_total)/plan_children_completed*100):.1f}%)\n"
            else:
                plan_text += f"  ✓ Исполнение по плану (100%)\n"
        else:
            plan_text += f"  (н/д - нет проведённых/отменённых)\n"
        
        plan_text += "\n"
        
        # Бюджет на тренеров (УЭВП)
        plan_text += "2. БЮДЖЕТ НА ТРЕНЕРОВ\n"
        plan_text += "   Источник финансирования: ф. УЭВП ООО \"Газпром добыча Ямбург\"\n"
        plan_text += "-" * 90 + "\n"
        plan_text += f"  Планируемые расходы: {format_rubles(plan_trainers_total)}\n"
        plan_text += f"  Фактические расходы: {format_rubles(fact_trainers_total)}\n"
        
        # Экономия/Перерасход только для проведённых/отменённых
        if plan_trainers_completed > 0:
            diff_trainers_total = plan_trainers_completed - fact_trainers_total
            if diff_trainers_total > 0:
                plan_text += f"  ✓ ЭКОНОМИЯ: {format_rubles(diff_trainers_total)} ({(diff_trainers_total/plan_trainers_completed*100):.1f}%)\n"
            elif diff_trainers_total < 0:
                plan_text += f"  ⚠ ПЕРЕРАСХОД: {format_rubles(abs(diff_trainers_total))} ({(abs(diff_trainers_total)/plan_trainers_completed*100):.1f}%)\n"
            else:
                plan_text += f"  ✓ Исполнение по плану (100%)\n"
        else:
            plan_text += f"  (н/д - нет проведённых/отменённых)\n"
        
        plan_text += "\n" + "=" * 90 + "\n"
        plan_text += "Примечание: Бюджеты финансируются из разных источников и не суммируются.\n"
        plan_text += "=" * 90 + "\n"
        
        # Отображаем план
        self.text_area.insert('1.0', plan_text)
    
    def _load_financial_report(self):
        """Финансовый отчёт - только бюджеты без деталей мероприятий"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        
        report_text = ""
        report_text += "=" * 90 + "\n"
        report_text += f"ФИНАНСОВЫЙ ОТЧЁТ НА {self.year} ГОД\n"
        report_text += "=" * 90 + "\n\n"
        
        # Статистика по видам спорта (только финансы)
        report_text += "ФИНАНСИРОВАНИЕ ПО ВИДАМ СПОРТА:\n"
        report_text += "=" * 90 + "\n"
        
        sport_stats = {}
        for event in events:
            if event.sport not in sport_stats:
                sport_stats[event.sport] = {
                    'count': 0,
                    'plan_children': 0,
                    'fact_children': 0,
                    'plan_trainers': 0,
                    'fact_trainers': 0,
                    'plan_children_completed': 0,  # План только для проведённых/отменённых
                    'plan_trainers_completed': 0   # План только для проведённых/отменённых
                }
            
            sport_stats[event.sport]['count'] += 1
            sport_stats[event.sport]['plan_children'] += event.children_budget
            sport_stats[event.sport]['plan_trainers'] += event.trainers_budget
            
            # Факт и план для проведённых/отменённых (для расчёта экономии/перерасхода)
            if event.status in ["Проведено", "Отменено"]:
                sport_stats[event.sport]['plan_children_completed'] += event.children_budget
                sport_stats[event.sport]['plan_trainers_completed'] += event.trainers_budget
                
                if event.status == "Проведено":
                    if event.actual_children_budget is not None:
                        sport_stats[event.sport]['fact_children'] += event.actual_children_budget
                    else:
                        # Если мероприятие проведено, но факт не указан - берём план
                        sport_stats[event.sport]['fact_children'] += event.children_budget
                    
                    if event.actual_trainers_budget is not None:
                        sport_stats[event.sport]['fact_trainers'] += event.actual_trainers_budget
                    else:
                        # Если мероприятие проведено, но факт не указан - берём план
                        sport_stats[event.sport]['fact_trainers'] += event.trainers_budget
                # Для отменённых факт = 0 (не тратили)
            # Для запланированных, перенесённых - факт = 0
        
        for sport in sorted(sport_stats.keys()):
            stats = sport_stats[sport]
            report_text += f"\n{sport} ({stats['count']} мероприятий):\n"
            report_text += f"  Бюджет детей:    {stats['plan_children']:>12.2f} → {stats['fact_children']:>12.2f}"
            
            # Экономия/Перерасход только для проведённых/отменённых
            if stats['plan_children_completed'] > 0:
                diff_c = stats['plan_children_completed'] - stats['fact_children']
                if diff_c > 0:
                    report_text += f"  (экономия: {diff_c:.2f})\n"
                elif diff_c < 0:
                    report_text += f"  (перерасход: {abs(diff_c):.2f})\n"
                else:
                    report_text += "\n"
            else:
                report_text += "  (н/д)\n"
            
            report_text += f"  Бюджет тренеров: {stats['plan_trainers']:>12.2f} → {stats['fact_trainers']:>12.2f}"
            
            # Экономия/Перерасход только для проведённых/отменённых
            if stats['plan_trainers_completed'] > 0:
                diff_t = stats['plan_trainers_completed'] - stats['fact_trainers']
                if diff_t > 0:
                    report_text += f"  (экономия: {diff_t:.2f})\n"
                elif diff_t < 0:
                    report_text += f"  (перерасход: {abs(diff_t):.2f})\n"
                else:
                    report_text += "\n"
            else:
                report_text += "  (н/д)\n"
        
        # Общие итоги
        report_text += "\n" + "=" * 90 + "\n"
        report_text += "ИТОГИ ПО БЮДЖЕТАМ:\n"
        report_text += "=" * 90 + "\n"
        
        plan_children_total = sum(e.children_budget for e in events)
        plan_trainers_total = sum(e.trainers_budget for e in events)
        
        # План для проведённых/отменённых (для расчёта экономии/перерасхода)
        plan_children_completed = sum(e.children_budget for e in events if e.status in ["Проведено", "Отменено"])
        plan_trainers_completed = sum(e.trainers_budget for e in events if e.status in ["Проведено", "Отменено"])
        
        # Факт только для проведённых
        fact_children_total = sum(
            e.actual_children_budget if e.actual_children_budget is not None else e.children_budget
            for e in events if e.status == "Проведено"
        )
        fact_trainers_total = sum(
            e.actual_trainers_budget if e.actual_trainers_budget is not None else e.trainers_budget
            for e in events if e.status == "Проведено"
        )
        
        report_text += "\n1. БЮДЖЕТ НА ДЕТЕЙ\n"
        report_text += "   Источник: ППО \"Газпром добыча Ямбург профсоюз\"\n"
        report_text += "-" * 90 + "\n"
        report_text += f"  План:  {format_rubles(plan_children_total):>25}\n"
        report_text += f"  Факт:  {format_rubles(fact_children_total):>25}\n"
        
        # Экономия/Перерасход только для проведённых/отменённых
        if plan_children_completed > 0:
            diff_children = plan_children_completed - fact_children_total
            if diff_children > 0:
                report_text += f"  ✓ ЭКОНОМИЯ: {format_rubles(diff_children)} ({(diff_children/plan_children_completed*100):.1f}%)\n"
            elif diff_children < 0:
                report_text += f"  ⚠ ПЕРЕРАСХОД: {format_rubles(abs(diff_children))} ({(abs(diff_children)/plan_children_completed*100):.1f}%)\n"
            else:
                report_text += f"  ✓ Исполнение по плану\n"
        else:
            report_text += f"  (н/д - нет проведённых/отменённых)\n"
        
        report_text += "\n2. БЮДЖЕТ НА ТРЕНЕРОВ\n"
        report_text += "   Источник: ф. УЭВП ООО \"Газпром добыча Ямбург\"\n"
        report_text += "-" * 90 + "\n"
        report_text += f"  План:  {format_rubles(plan_trainers_total):>25}\n"
        report_text += f"  Факт:  {format_rubles(fact_trainers_total):>25}\n"
        
        # Экономия/Перерасход только для проведённых/отменённых
        if plan_trainers_completed > 0:
            diff_trainers = plan_trainers_completed - fact_trainers_total
            if diff_trainers > 0:
                report_text += f"  ✓ ЭКОНОМИЯ: {format_rubles(diff_trainers)} ({(diff_trainers/plan_trainers_completed*100):.1f}%)\n"
            elif diff_trainers < 0:
                report_text += f"  ⚠ ПЕРЕРАСХОД: {format_rubles(abs(diff_trainers))} ({(abs(diff_trainers)/plan_trainers_completed*100):.1f}%)\n"
            else:
                report_text += f"  ✓ Исполнение по плану\n"
        else:
            report_text += f"  (н/д - нет проведённых/отменённых)\n"
        
        report_text += "\n" + "=" * 90 + "\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _load_sports_report(self):
        """Отчёт по видам спорта"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        
        report_text = ""
        report_text += "=" * 90 + "\n"
        report_text += f"ОТЧЁТ ПО ВИДАМ СПОРТА - {self.year} ГОД\n"
        report_text += "=" * 90 + "\n\n"
        
        # Группируем по видам спорта
        sports_dict = {}
        for event in events:
            if event.sport not in sports_dict:
                sports_dict[event.sport] = []
            sports_dict[event.sport].append(event)
        
        for sport in sorted(sports_dict.keys()):
            sport_events = sports_dict[sport]
            
            report_text += "=" * 90 + "\n"
            report_text += f"{sport.upper()} ({len(sport_events)} мероприятий)\n"
            report_text += "=" * 90 + "\n\n"
            
            # Статистика
            conducted = sum(1 for e in sport_events if e.status == "Проведено")
            cancelled = sum(1 for e in sport_events if e.status == "Отменено")
            postponed = sum(1 for e in sport_events if e.status == "Перенесено")
            planned = sum(1 for e in sport_events if e.status == "Запланировано")
            
            report_text += f"Статистика:\n"
            report_text += f"  Проведено: {conducted}\n"
            if cancelled > 0:
                report_text += f"  Отменено: {cancelled}\n"
            if postponed > 0:
                report_text += f"  Перенесено: {postponed}\n"
            report_text += f"  Запланировано: {planned}\n\n"
            
            # Список мероприятий
            report_text += "Мероприятия:\n"
            report_text += "-" * 90 + "\n"
            
            for i, event in enumerate(sport_events, 1):
                status_mark = {
                    "Проведено": "✓",
                    "Отменено": "✗",
                    "Перенесено": "→",
                    "Запланировано": "○"
                }.get(event.status, "○")
                
                report_text += f"{i}. [{status_mark}] {event.name}\n"
                report_text += f"   {event.event_type} | {event.month} | {event.location}\n"
                
                if event.actual_start_date:
                    report_text += f"   Даты: {event.actual_start_date}"
                    if event.actual_end_date and event.actual_end_date != event.actual_start_date:
                        report_text += f" - {event.actual_end_date}"
                    report_text += "\n"
                
                if event.cancellation_reason:
                    report_text += f"   Причина отмены: {event.cancellation_reason}\n"
                
                report_text += "\n"
            
            # Финансы по спорту
            plan_c = sum(e.children_budget for e in sport_events)
            plan_t = sum(e.trainers_budget for e in sport_events)
            
            # Факт только для проведённых мероприятий
            fact_c = sum(
                e.actual_children_budget if e.actual_children_budget is not None else e.children_budget
                for e in sport_events if e.status == "Проведено"
            )
            fact_t = sum(
                e.actual_trainers_budget if e.actual_trainers_budget is not None else e.trainers_budget
                for e in sport_events if e.status == "Проведено"
            )
            
            report_text += "Финансирование:\n"
            report_text += f"  Дети:    план {plan_c:.2f} → факт {fact_c:.2f}\n"
            report_text += f"  Тренеры: план {plan_t:.2f} → факт {fact_t:.2f}\n"
            report_text += "\n\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _load_status_report(self):
        """Отчёт по статусам мероприятий"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        
        report_text = ""
        report_text += "=" * 90 + "\n"
        report_text += f"ОТЧЁТ ПО СТАТУСАМ МЕРОПРИЯТИЙ - {self.year} ГОД\n"
        report_text += "=" * 90 + "\n\n"
        
        # Группируем по статусам
        status_dict = {}
        for event in events:
            status = event.status or "Запланировано"
            if status not in status_dict:
                status_dict[status] = []
            status_dict[status].append(event)
        
        # Порядок статусов
        status_order = ["Проведено", "Запланировано", "Перенесено", "Отменено"]
        
        for status in status_order:
            if status not in status_dict:
                continue
            
            status_events = status_dict[status]
            
            report_text += "=" * 90 + "\n"
            report_text += f"{status.upper()} ({len(status_events)} мероприятий)\n"
            report_text += "=" * 90 + "\n\n"
            
            # Группируем по месяцам
            by_month = {}
            for event in status_events:
                if event.month not in by_month:
                    by_month[event.month] = []
                by_month[event.month].append(event)
            
            for month in MONTHS:
                if month not in by_month:
                    continue
                
                month_events = by_month[month]
                report_text += f"{month}:\n"
                
                for event in month_events:
                    report_text += f"  • {event.name}\n"
                    report_text += f"    {event.sport} | {event.event_type} | {event.location}\n"
                    
                    if status == "Проведено" and event.actual_start_date:
                        report_text += f"    Даты: {event.actual_start_date}"
                        if event.actual_end_date and event.actual_end_date != event.actual_start_date:
                            report_text += f" - {event.actual_end_date}"
                        report_text += "\n"
                    
                    if status == "Отменено" and event.cancellation_reason:
                        report_text += f"    Причина: {event.cancellation_reason}\n"
                    
                    if status == "Перенесено" and event.postponement_reason:
                        report_text += f"    Причина: {event.postponement_reason}\n"
                    
                    report_text += "\n"
            
            report_text += "\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _load_summary_report(self):
        """Краткая сводка"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        
        report_text = ""
        report_text += "=" * 90 + "\n"
        report_text += f"КРАТКАЯ СВОДКА - {self.year} ГОД\n"
        report_text += "=" * 90 + "\n\n"
        
        # Общая статистика
        total = len(events)
        internal = sum(1 for e in events if e.event_type == "Внутреннее")
        external = sum(1 for e in events if e.event_type == "Выездное")
        
        conducted = sum(1 for e in events if e.status == "Проведено")
        cancelled = sum(1 for e in events if e.status == "Отменено")
        postponed = sum(1 for e in events if e.status == "Перенесено")
        planned = sum(1 for e in events if e.status == "Запланировано")
        
        report_text += "ОБЩАЯ СТАТИСТИКА:\n"
        report_text += "-" * 90 + "\n"
        report_text += f"Всего мероприятий: {total}\n"
        report_text += f"  Внутренних: {internal} ({internal/total*100:.1f}%)\n"
        report_text += f"  Выездных: {external} ({external/total*100:.1f}%)\n\n"
        
        report_text += "По статусам:\n"
        report_text += f"  Проведено: {conducted} ({conducted/total*100:.1f}%)\n"
        if cancelled > 0:
            report_text += f"  Отменено: {cancelled} ({cancelled/total*100:.1f}%)\n"
        if postponed > 0:
            report_text += f"  Перенесено: {postponed} ({postponed/total*100:.1f}%)\n"
        report_text += f"  Запланировано: {planned} ({planned/total*100:.1f}%)\n\n"
        
        # По видам спорта
        report_text += "ПО ВИДАМ СПОРТА:\n"
        report_text += "-" * 90 + "\n"
        
        sport_counts = {}
        for event in events:
            sport_counts[event.sport] = sport_counts.get(event.sport, 0) + 1
        
        for sport in sorted(sport_counts.keys()):
            count = sport_counts[sport]
            report_text += f"  {sport:.<30} {count:>3} ({count/total*100:>5.1f}%)\n"
        
        # Финансы
        report_text += "\n" + "=" * 90 + "\n"
        report_text += "ФИНАНСОВАЯ СВОДКА:\n"
        report_text += "=" * 90 + "\n\n"
        
        plan_children = sum(e.children_budget for e in events)
        plan_trainers = sum(e.trainers_budget for e in events)
        
        # План для проведённых/отменённых (для расчёта экономии/перерасхода)
        plan_children_completed = sum(e.children_budget for e in events if e.status in ["Проведено", "Отменено"])
        plan_trainers_completed = sum(e.trainers_budget for e in events if e.status in ["Проведено", "Отменено"])
        
        # Факт только для проведённых
        fact_children = sum(
            e.actual_children_budget if e.actual_children_budget is not None else e.children_budget
            for e in events if e.status == "Проведено"
        )
        fact_trainers = sum(
            e.actual_trainers_budget if e.actual_trainers_budget is not None else e.trainers_budget
            for e in events if e.status == "Проведено"
        )
        
        report_text += "Бюджет на детей (ППО \"Газпром добыча Ямбург профсоюз\"):\n"
        report_text += f"  План:  {format_rubles(plan_children):>25}\n"
        report_text += f"  Факт:  {format_rubles(fact_children):>25}\n"
        
        # Экономия/Перерасход только для проведённых/отменённых
        if plan_children_completed > 0:
            diff_c = plan_children_completed - fact_children
            if diff_c > 0:
                report_text += f"  ✓ Экономия:   {format_rubles(diff_c)} ({diff_c/plan_children_completed*100:>5.1f}%)\n"
            elif diff_c < 0:
                report_text += f"  ⚠ Перерасход: {format_rubles(abs(diff_c))} ({abs(diff_c)/plan_children_completed*100:>5.1f}%)\n"
            else:
                report_text += f"  ✓ По плану\n"
        else:
            report_text += f"  (н/д - нет проведённых/отменённых)\n"
        
        report_text += "\nБюджет на тренеров (ф. УЭВП ООО \"Газпром добыча Ямбург\"):\n"
        report_text += f"  План:  {format_rubles(plan_trainers):>25}\n"
        report_text += f"  Факт:  {format_rubles(fact_trainers):>25}\n"
        
        # Экономия/Перерасход только для проведённых/отменённых
        if plan_trainers_completed > 0:
            diff_t = plan_trainers_completed - fact_trainers
            if diff_t > 0:
                report_text += f"  ✓ Экономия:   {format_rubles(diff_t)} ({diff_t/plan_trainers_completed*100:>5.1f}%)\n"
            elif diff_t < 0:
                report_text += f"  ⚠ Перерасход: {format_rubles(abs(diff_t))} ({abs(diff_t)/plan_trainers_completed*100:>5.1f}%)\n"
            else:
                report_text += f"  ✓ По плану\n"
        else:
            report_text += f"  (н/д - нет проведённых/отменённых)\n"
        
        report_text += "\n" + "=" * 90 + "\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _load_by_type_report(self):
        """Финансовый отчёт по типам мероприятий (выездные/внутренние) для каждого вида спорта"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        
        report_text = ""
        report_text += "=" * 90 + "\n"
        report_text += f"ФИНАНСОВЫЙ ОТЧЁТ ПО ТИПАМ МЕРОПРИЯТИЙ - {self.year} ГОД\n"
        report_text += "=" * 90 + "\n\n"
        
        # Собираем статистику по видам спорта и типам мероприятий
        sport_stats = {}
        
        for event in events:
            if event.sport not in sport_stats:
                sport_stats[event.sport] = {
                    'Внутреннее': {
                        'count': 0,
                        'plan_children': 0,
                        'fact_children': 0,
                        'plan_trainers': 0,
                        'fact_trainers': 0,
                        'plan_children_completed': 0,
                        'plan_trainers_completed': 0
                    },
                    'Выездное': {
                        'count': 0,
                        'plan_children': 0,
                        'fact_children': 0,
                        'plan_trainers': 0,
                        'fact_trainers': 0,
                        'plan_children_completed': 0,
                        'plan_trainers_completed': 0
                    }
                }
            
            event_type = event.event_type
            stats = sport_stats[event.sport][event_type]
            
            stats['count'] += 1
            stats['plan_children'] += event.children_budget
            stats['plan_trainers'] += event.trainers_budget
            
            # Факт и план для проведённых/отменённых
            if event.status in ["Проведено", "Отменено"]:
                stats['plan_children_completed'] += event.children_budget
                stats['plan_trainers_completed'] += event.trainers_budget
                
                if event.status == "Проведено":
                    if event.actual_children_budget is not None:
                        stats['fact_children'] += event.actual_children_budget
                    else:
                        stats['fact_children'] += event.children_budget
                    
                    if event.actual_trainers_budget is not None:
                        stats['fact_trainers'] += event.actual_trainers_budget
                    else:
                        stats['fact_trainers'] += event.trainers_budget
        
        # Выводим отчёт по каждому виду спорта
        for sport in sorted(sport_stats.keys()):
            report_text += f"{'=' * 90}\n"
            report_text += f"{sport.upper()}\n"
            report_text += f"{'=' * 90}\n\n"
            
            for event_type in ['Внутреннее', 'Выездное']:
                stats = sport_stats[sport][event_type]
                
                if stats['count'] == 0:
                    continue
                
                report_text += f"  {event_type} ({stats['count']} мероприятий)\n"
                report_text += f"  {'-' * 86}\n"
                
                # Бюджет на детей
                report_text += f"  Бюджет на детей:\n"
                report_text += f"    План: {format_rubles(stats['plan_children']):>30}\n"
                report_text += f"    Факт: {format_rubles(stats['fact_children']):>30}\n"
                
                if stats['plan_children_completed'] > 0:
                    diff_c = stats['plan_children_completed'] - stats['fact_children']
                    if diff_c > 0:
                        report_text += f"    ✓ Экономия:   {format_rubles(diff_c):>30} ({diff_c/stats['plan_children_completed']*100:>5.1f}%)\n"
                    elif diff_c < 0:
                        report_text += f"    ⚠ Перерасход: {format_rubles(abs(diff_c)):>30} ({abs(diff_c)/stats['plan_children_completed']*100:>5.1f}%)\n"
                    else:
                        report_text += f"    ✓ По плану\n"
                else:
                    report_text += f"    (н/д - нет проведённых/отменённых)\n"
                
                # Бюджет на тренеров
                report_text += f"\n  Бюджет на тренеров:\n"
                report_text += f"    План: {format_rubles(stats['plan_trainers']):>30}\n"
                report_text += f"    Факт: {format_rubles(stats['fact_trainers']):>30}\n"
                
                if stats['plan_trainers_completed'] > 0:
                    diff_t = stats['plan_trainers_completed'] - stats['fact_trainers']
                    if diff_t > 0:
                        report_text += f"    ✓ Экономия:   {format_rubles(diff_t):>30} ({diff_t/stats['plan_trainers_completed']*100:>5.1f}%)\n"
                    elif diff_t < 0:
                        report_text += f"    ⚠ Перерасход: {format_rubles(abs(diff_t)):>30} ({abs(diff_t)/stats['plan_trainers_completed']*100:>5.1f}%)\n"
                    else:
                        report_text += f"    ✓ По плану\n"
                else:
                    report_text += f"    (н/д - нет проведённых/отменённых)\n"
                
                report_text += "\n"
            
            report_text += "\n"
        
        # Общие итоги по типам мероприятий
        report_text += "=" * 90 + "\n"
        report_text += "ОБЩИЕ ИТОГИ ПО ТИПАМ МЕРОПРИЯТИЙ\n"
        report_text += "=" * 90 + "\n\n"
        
        # Суммируем по типам
        type_totals = {
            'Внутреннее': {
                'count': 0,
                'plan_children': 0,
                'fact_children': 0,
                'plan_trainers': 0,
                'fact_trainers': 0,
                'plan_children_completed': 0,
                'plan_trainers_completed': 0
            },
            'Выездное': {
                'count': 0,
                'plan_children': 0,
                'fact_children': 0,
                'plan_trainers': 0,
                'fact_trainers': 0,
                'plan_children_completed': 0,
                'plan_trainers_completed': 0
            }
        }
        
        for sport in sport_stats:
            for event_type in ['Внутреннее', 'Выездное']:
                stats = sport_stats[sport][event_type]
                type_totals[event_type]['count'] += stats['count']
                type_totals[event_type]['plan_children'] += stats['plan_children']
                type_totals[event_type]['fact_children'] += stats['fact_children']
                type_totals[event_type]['plan_trainers'] += stats['plan_trainers']
                type_totals[event_type]['fact_trainers'] += stats['fact_trainers']
                type_totals[event_type]['plan_children_completed'] += stats['plan_children_completed']
                type_totals[event_type]['plan_trainers_completed'] += stats['plan_trainers_completed']
        
        for event_type in ['Внутреннее', 'Выездное']:
            totals = type_totals[event_type]
            
            if totals['count'] == 0:
                continue
            
            report_text += f"{event_type.upper()} МЕРОПРИЯТИЯ ({totals['count']} шт.)\n"
            report_text += f"{'-' * 90}\n\n"
            
            # Бюджет на детей
            report_text += "Бюджет на детей (ППО \"Газпром добыча Ямбург профсоюз\"):\n"
            report_text += f"  План:  {format_rubles(totals['plan_children']):>30}\n"
            report_text += f"  Факт:  {format_rubles(totals['fact_children']):>30}\n"
            
            if totals['plan_children_completed'] > 0:
                diff_c = totals['plan_children_completed'] - totals['fact_children']
                if diff_c > 0:
                    report_text += f"  ✓ ЭКОНОМИЯ:   {format_rubles(diff_c):>30} ({diff_c/totals['plan_children_completed']*100:>5.1f}%)\n"
                elif diff_c < 0:
                    report_text += f"  ⚠ ПЕРЕРАСХОД: {format_rubles(abs(diff_c)):>30} ({abs(diff_c)/totals['plan_children_completed']*100:>5.1f}%)\n"
                else:
                    report_text += f"  ✓ ПО ПЛАНУ\n"
            else:
                report_text += f"  (н/д - нет проведённых/отменённых)\n"
            
            # Бюджет на тренеров
            report_text += f"\nБюджет на тренеров (ф. УЭВП ООО \"Газпром добыча Ямбург\"):\n"
            report_text += f"  План:  {format_rubles(totals['plan_trainers']):>30}\n"
            report_text += f"  Факт:  {format_rubles(totals['fact_trainers']):>30}\n"
            
            if totals['plan_trainers_completed'] > 0:
                diff_t = totals['plan_trainers_completed'] - totals['fact_trainers']
                if diff_t > 0:
                    report_text += f"  ✓ ЭКОНОМИЯ:   {format_rubles(diff_t):>30} ({diff_t/totals['plan_trainers_completed']*100:>5.1f}%)\n"
                elif diff_t < 0:
                    report_text += f"  ⚠ ПЕРЕРАСХОД: {format_rubles(abs(diff_t)):>30} ({abs(diff_t)/totals['plan_trainers_completed']*100:>5.1f}%)\n"
                else:
                    report_text += f"  ✓ ПО ПЛАНУ\n"
            else:
                report_text += f"  (н/д - нет проведённых/отменённых)\n"
            
            report_text += "\n"
        
        report_text += "=" * 90 + "\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _load_annual_ppo_report(self):
        """Годовой отчет ППО - расчет плановых затрат с разбивкой по кварталам и детализацией смет"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        
        # Разделяем на выездные и внутренние
        away_events = [e for e in events if e.event_type == "Выездное"]
        internal_events = [e for e in events if e.event_type == "Внутреннее"]
        
        report_text = ""
        report_text += "=" * 180 + "\n"
        report_text += f"РАСЧЕТ ПЛАНОВЫХ ЗАТРАТ НА {self.year} ГОД\n"
        report_text += f"НА ПРОВЕДЕНИЕ КУЛЬТУРНО-МАССОВЫХ МЕРОПРИЯТИЙ ДЮСК \"ЯМБУРГ\" ППО \"ГАЗПРОМ ДОБЫЧА ЯМБУРГ ПРОФСОЮЗ\"\n"
        report_text += "=" * 180 + "\n\n"
        
        # Заголовок таблицы
        report_text += f"{'№':<6} {'Наименование статей затрат/Мероприятий':<60} {'Место/Ед.изм.':<20} {'Даты/Кол-во':<12} {'Стоим.':<10} {'Чел.':<5} "
        report_text += f"{'Затраты (руб)':>15} {'1 кв.':>15} {'2 кв.':>15} {'3 кв.':>15} {'4 кв.':>15}\n"
        report_text += "=" * 180 + "\n\n"
        
        # Определяем месяцы по кварталам
        q1_months = ['Январь', 'Февраль', 'Март']
        q2_months = ['Апрель', 'Май', 'Июнь']
        q3_months = ['Июль', 'Август', 'Сентябрь']
        q4_months = ['Октябрь', 'Ноябрь', 'Декабрь']
        
        def get_quarter(month):
            if month in q1_months: return 1
            if month in q2_months: return 2
            if month in q3_months: return 3
            if month in q4_months: return 4
            return 1
        
        # Раздел 1: Выездные мероприятия
        if away_events:
            report_text += "1.   ВЫЕЗДНЫЕ МЕРОПРИЯТИЯ\n"
            report_text += "-" * 180 + "\n\n"
            
            # Предварительный расчёт итогов по выездным
            away_q_totals = {1: 0, 2: 0, 3: 0, 4: 0}
            away_total = 0
            for event in away_events:
                quarter = get_quarter(event.month)
                away_q_totals[quarter] += event.children_budget
                away_total += event.children_budget
            
            # Синяя итоговая строка с суммами по кварталам
            report_text += f"{'':<101} "
            report_text += f"{format_rubles(away_total):>15} {format_rubles(away_q_totals[1]):>15} {format_rubles(away_q_totals[2]):>15} "
            report_text += f"{format_rubles(away_q_totals[3]):>15} {format_rubles(away_q_totals[4]):>15}\n"
            report_text += "-" * 180 + "\n\n"
            
            q_totals = {1: 0, 2: 0, 3: 0, 4: 0}
            total_all = 0
            
            for idx, event in enumerate(away_events, 1):
                quarter = get_quarter(event.month)
                
                # Получаем смету ППО для мероприятия
                estimates = self.db.get_estimates_by_event(event.id)
                ppo_estimate = None
                for est in estimates:
                    if est[2] == 'ППО':  # estimate_type
                        ppo_estimate = est
                        break
                
                # Название мероприятия (с трёхзначной нумерацией: 1.001, 1.002, и т.д.)
                report_text += f"1.{idx:03d}  {event.name[:57]:<60} {event.location:<20} {event.month:<12} {'':>10} {'':>5} "
                q_vals = [''] * 4
                q_vals[quarter-1] = format_rubles(event.children_budget)
                report_text += f"{format_rubles(event.children_budget):>15} {q_vals[0]:>15} {q_vals[1]:>15} {q_vals[2]:>15} {q_vals[3]:>15}\n"
                
                # Детализация по смете
                if ppo_estimate:
                    estimate_id = ppo_estimate[0]
                    items = self.db.get_estimate_items(estimate_id)
                    
                    for item in items:
                        category = item[2]
                        description = item[3] or ''
                        people_count = item[4] or 0
                        days_count = item[5] or 0
                        rate = item[6] or 0
                        total = item[7] or 0
                        
                        # Форматируем вывод
                        if category == "Проезд":
                            report_text += f"       {category:<57} {description:<20} {days_count:<12} {rate:>10.0f} {people_count:<5}\n"
                        elif category == "Проживание":
                            report_text += f"       {category:<57} {'дн':<20} {days_count:<12} {rate:>10.0f} {people_count:<5}\n"
                        elif category == "Суточные":
                            report_text += f"       {category:<57} {'дн':<20} {days_count:<12} {rate:>10.0f} {people_count:<5}\n"
                
                report_text += "\n"
                q_totals[quarter] += event.children_budget
                total_all += event.children_budget
            
            report_text += f"{'ИТОГО выездные:':<101} "
            report_text += f"{format_rubles(total_all):>15} {format_rubles(q_totals[1]):>15} {format_rubles(q_totals[2]):>15} "
            report_text += f"{format_rubles(q_totals[3]):>15} {format_rubles(q_totals[4]):>15}\n"
            report_text += "\n" + "=" * 180 + "\n\n"
        
        # Раздел 2: Внутренние мероприятия
        if internal_events:
            report_text += "2.   ВНУТРЕННИЕ И ГОРОДСКИЕ МЕРОПРИЯТИЯ\n"
            report_text += "-" * 180 + "\n\n"
            
            # Предварительный расчёт итогов по внутренним
            internal_q_totals = {1: 0, 2: 0, 3: 0, 4: 0}
            internal_total = 0
            for event in internal_events:
                quarter = get_quarter(event.month)
                internal_q_totals[quarter] += event.children_budget
                internal_total += event.children_budget
            
            # Синяя итоговая строка с суммами по кварталам
            report_text += f"{'':<101} "
            report_text += f"{format_rubles(internal_total):>15} {format_rubles(internal_q_totals[1]):>15} {format_rubles(internal_q_totals[2]):>15} "
            report_text += f"{format_rubles(internal_q_totals[3]):>15} {format_rubles(internal_q_totals[4]):>15}\n"
            report_text += "-" * 180 + "\n\n"
            
            q_totals = {1: 0, 2: 0, 3: 0, 4: 0}
            total_all = 0
            
            for idx, event in enumerate(internal_events, 1):
                quarter = get_quarter(event.month)
                
                # Получаем смету ППО для мероприятия
                estimates = self.db.get_estimates_by_event(event.id)
                ppo_estimate = None
                for est in estimates:
                    if est[2] == 'ППО':  # estimate_type
                        ppo_estimate = est
                        break
                
                # Название мероприятия (трёхзначная нумерация: 2.001, 2.002, и т.д.)
                report_text += f"2.{idx:03d}  {event.name[:57]:<60} {event.location:<20} {event.month:<12} {'':>10} {'':>5} "
                q_vals = [''] * 4
                q_vals[quarter-1] = format_rubles(event.children_budget)
                report_text += f"{format_rubles(event.children_budget):>15} {q_vals[0]:>15} {q_vals[1]:>15} {q_vals[2]:>15} {q_vals[3]:>15}\n"
                
                # Детализация по смете
                if ppo_estimate:
                    estimate_id = ppo_estimate[0]
                    items = self.db.get_estimate_items(estimate_id)
                    
                    for item in items:
                        category = item[2]
                        description = item[3] or ''
                        people_count = item[4] or 0
                        days_count = item[5] or 0
                        rate = item[6] or 0
                        total = item[7] or 0
                        
                        # Форматируем вывод - для внутренних выводим категорию и описание
                        report_text += f"       {category:<57} {description[:20]:<20} {days_count:<12} {rate:>10.0f} {people_count:<5}\n"
                
                report_text += "\n"
                q_totals[quarter] += event.children_budget
                total_all += event.children_budget
            
            report_text += "\n"
            report_text += f"{'ИТОГО внутренние:':<101} "
            report_text += f"{format_rubles(total_all):>15} {format_rubles(q_totals[1]):>15} {format_rubles(q_totals[2]):>15} "
            report_text += f"{format_rubles(q_totals[3]):>15} {format_rubles(q_totals[4]):>15}\n"
            report_text += "\n" + "=" * 180 + "\n\n"
        
        # Общий итог
        grand_total = sum(e.children_budget for e in events)
        grand_q_totals = {1: 0, 2: 0, 3: 0, 4: 0}
        for event in events:
            quarter = get_quarter(event.month)
            grand_q_totals[quarter] += event.children_budget
        
        report_text += f"{'ВСЕГО ИТОГО:':<101} "
        report_text += f"{format_rubles(grand_total):>15} {format_rubles(grand_q_totals[1]):>15} {format_rubles(grand_q_totals[2]):>15} "
        report_text += f"{format_rubles(grand_q_totals[3]):>15} {format_rubles(grand_q_totals[4]):>15}\n"
        report_text += "=" * 180 + "\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _load_annual_uevp_report(self):
        """Годовой отчет УЭВП - расчет плановых затрат с детализацией по мероприятиям"""
        events_data = self.db.get_events_by_year(self.year)
        
        if not events_data:
            self.text_area.insert('1.0', "Нет мероприятий на этот год")
            return
        
        events = [Event.from_db_row(row) for row in events_data]
        # Только выездные мероприятия
        away_events = [e for e in events if e.event_type == "Выездное"]
        
        if not away_events:
            self.text_area.insert('1.0', "Нет выездных мероприятий на этот год")
            return
        
        report_text = ""
        report_text += "=" * 250 + "\n"
        report_text += f"ОТЧЕТ ПО КОМАНДИРОВКАМ ТРЕНЕРОВ ДЮСК \"ЯМБУРГ\" ЗА {self.year} ГОД (Ф. УЭВП)\n"
        report_text += "=" * 250 + "\n\n"
        
        # Заголовок таблицы
        report_text += f"{'Должность':<20} {'Месяц':<12} {'Дни':<6} {'Город':<25} {'Цель командировки':<50} "
        report_text += f"{'Проезд':>12} {'Проживание':>12} {'Суточные':>12} {'Итого':>12} {'Факт':>12} {'Эк/Пер':>12}\n"
        report_text += "=" * 250 + "\n"
        
        total_proezd = 0
        total_prozhivanie = 0
        total_sutochnie = 0
        total_all = 0
        total_fact = 0
        
        # Собираем данные по каждому мероприятию
        for event in away_events:
            # Получаем смету УЭВП для этого мероприятия
            estimate_data = self.db.cursor.execute('''
                SELECT id, total_amount
                FROM estimates
                WHERE event_id = ? AND estimate_type = 'УЭВП'
            ''', (event.id,)).fetchone()
            
            if not estimate_data:
                continue
            
            estimate_id = estimate_data[0]
            
            # Получаем детали сметы (проезд, проживание, суточные)
            items = self.db.cursor.execute('''
                SELECT category, SUM(total) as total, MAX(days_count) as days
                FROM estimate_items
                WHERE estimate_id = ?
                GROUP BY category
            ''', (estimate_id,)).fetchall()
            
            proezd = 0
            prozhivanie = 0
            sutochnie = 0
            days = 0
            
            for category, total, day_count in items:
                if category == 'Проезд':
                    proezd = total
                elif category == 'Проживание':
                    prozhivanie = total
                    days = day_count or days
                elif category == 'Суточные':
                    sutochnie = total
                    days = day_count or days
            
            # Если дни не определены, ставим по умолчанию
            if days == 0:
                days = 5
            
            # Формируем цель командировки
            purpose = f"Сопровождение спортсменов для участия в {event.name} по виду спорта {event.sport}"
            if len(purpose) > 48:
                purpose = purpose[:47] + "..."
            
            # Итого по мероприятию
            event_total = proezd + prozhivanie + sutochnie
            
            # Фактические расходы - только для проведённых и отменённых
            fact = ""
            economy = ""
            if event.status in ["Проведено", "Отменено"]:
                fact_amount = event.actual_trainers_budget if event.actual_trainers_budget is not None else event_total
                fact = f"{fact_amount:>12.2f}"
                economy_amount = event_total - fact_amount
                economy = f"{economy_amount:>+12.2f}" if economy_amount != 0 else f"{'0.00':>12}"
                total_fact += fact_amount
            else:
                fact = f"{'-':>12}"
                economy = f"{'-':>12}"
            
            # Печатаем строку
            report_text += f"{'Тренер':<20} {event.month:<12} {days:<6} {event.location[:24]:<25} "
            report_text += f"{purpose:<50} {proezd:>12.2f} {prozhivanie:>12.2f} {sutochnie:>12.2f} "
            report_text += f"{event_total:>12.2f} {fact} {economy}\n"
            
            total_proezd += proezd
            total_prozhivanie += prozhivanie
            total_sutochnie += sutochnie
            total_all += event_total
        
        report_text += "=" * 250 + "\n"
        
        # Итого
        report_text += f"{'ИТОГО:':<20} {'':<12} {'':<6} {'':<25} {'':<50} "
        report_text += f"{total_proezd:>12.2f} {total_prozhivanie:>12.2f} {total_sutochnie:>12.2f} "
        report_text += f"{total_all:>12.2f} "
        
        if total_fact > 0:
            total_economy = total_all - total_fact
            report_text += f"{total_fact:>12.2f} {total_economy:>+12.2f}\n"
        else:
            report_text += f"{'-':>12} {'-':>12}\n"
        
        report_text += "=" * 250 + "\n"
        
        self.text_area.insert('1.0', report_text)
    
    def _save_report(self, format_type):
        """
        Сохранить отчёт в файл
        
        Args:
            format_type: Формат файла ('txt', 'csv', 'html')
        """
        # Определяем расширение и фильтр
        extensions = {
            'txt': ('Текстовый файл', '*.txt'),
            'csv': ('CSV файл', '*.csv'),
            'html': ('HTML файл', '*.html')
        }
        
        report_names = {
            'full': 'Полный_план',
            'financial': 'Финансовый_отчёт',
            'sports': 'По_видам_спорта',
            'status': 'По_статусам',
            'summary': 'Краткая_сводка',
            'by_type': 'По_типам_мероприятий',
            'annual_ppo': 'Годовой_отчет_ППО',
            'annual_uevp': 'Годовой_отчет_УЭВП'
        }
        
        default_name = f"calendar_{self.year}_{report_names.get(self.current_report_type, 'report')}"
        
        # Диалог сохранения
        filename = filedialog.asksaveasfilename(
            title="Сохранить отчёт",
            defaultextension=f".{format_type}",
            filetypes=[extensions[format_type], ("Все файлы", "*.*")],
            initialfile=f"{default_name}.{format_type}"
        )
        
        if not filename:
            return
        
        try:
            if format_type == 'txt':
                self._save_as_txt(filename)
            elif format_type == 'csv':
                self._save_as_csv(filename)
            elif format_type == 'html':
                self._save_as_html(filename)
                # Автоматически открываем HTML в браузере
                try:
                    # Преобразуем путь в абсолютный URL для браузера
                    abs_path = os.path.abspath(filename)
                    webbrowser.open('file://' + abs_path)
                    messagebox.showinfo("Успешно", f"Отчёт сохранён и открыт в браузере:\n{filename}")
                except Exception as browser_error:
                    messagebox.showinfo("Успешно", f"Отчёт сохранён:\n{filename}\n\nНе удалось открыть браузер автоматически.")
                return  # Выходим, чтобы не показывать второе сообщение
            
            messagebox.showinfo("Успешно", f"Отчёт сохранён:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")
    
    def _save_as_txt(self, filename):
        """Сохранить отчёт как текстовый файл"""
        content = self.text_area.get('1.0', tk.END)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _save_as_csv(self, filename):
        """Сохранить отчёт как CSV"""
        events_data = self.db.get_events_by_year(self.year)
        events = [Event.from_db_row(row) for row in events_data]
        
        # Фильтруем события в зависимости от типа отчета
        if self.current_report_type == 'financial':
            # Для финансового отчета - все события, но только финансовые данные
            filtered_events = events
        elif self.current_report_type == 'sports':
            # Для отчета по спортам - все события
            filtered_events = events
        elif self.current_report_type == 'status':
            # Для отчета по статусам - все события
            filtered_events = events
        elif self.current_report_type == 'summary':
            # Для краткой сводки - все события
            filtered_events = events
        elif self.current_report_type == 'by_type':
            # Для отчета по типам - все события
            filtered_events = events
        elif self.current_report_type == 'annual_ppo':
            # Для годового отчета ППО - все события
            filtered_events = events
        elif self.current_report_type == 'annual_uevp':
            # Для годового отчета УЭВП - только выездные
            filtered_events = [e for e in events if e.event_type == "Выездное"]
        else:  # 'full'
            filtered_events = events
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Заголовки зависят от типа отчета
            if self.current_report_type == 'financial':
                writer.writerow([
                    'Вид спорта', 'Мероприятий',
                    'План: детей (₽)', 'Факт: детей (₽)', 'Экономия/Перерасход ППО', 'Остаток ППО',
                    'План: тренеры (₽)', 'Факт: тренеры (₽)', 'Экономия/Перерасход УЭВП', 'Остаток УЭВП'
                ])
                
                # Группируем по видам спорта
                sport_stats = {}
                for event in filtered_events:
                    if event.sport not in sport_stats:
                        sport_stats[event.sport] = {
                            'count': 0, 
                            'plan_children': 0, 'fact_children': 0,
                            'plan_trainers': 0, 'fact_trainers': 0,
                            'plan_children_completed': 0,  # План только для проведённых/отменённых
                            'plan_trainers_completed': 0   # План только для проведённых/отменённых
                        }
                    
                    sport_stats[event.sport]['count'] += 1
                    sport_stats[event.sport]['plan_children'] += event.children_budget
                    sport_stats[event.sport]['plan_trainers'] += event.trainers_budget
                    
                    # Факт и план для проведённых/отменённых (для расчёта экономии/перерасхода)
                    if event.status in ["Проведено", "Отменено"]:
                        sport_stats[event.sport]['plan_children_completed'] += event.children_budget
                        sport_stats[event.sport]['plan_trainers_completed'] += event.trainers_budget
                        
                        if event.status == "Проведено":
                            if event.actual_children_budget is not None:
                                sport_stats[event.sport]['fact_children'] += event.actual_children_budget
                            else:
                                # Если мероприятие проведено, но факт не указан - берём план
                                sport_stats[event.sport]['fact_children'] += event.children_budget
                            
                            if event.actual_trainers_budget is not None:
                                sport_stats[event.sport]['fact_trainers'] += event.actual_trainers_budget
                            else:
                                # Если мероприятие проведено, но факт не указан - берём план
                                sport_stats[event.sport]['fact_trainers'] += event.trainers_budget
                        # Для отменённых факт = 0 (не тратили)
                    # Для запланированных, перенесённых - факт = 0
                
                for sport in sorted(sport_stats.keys()):
                    stats = sport_stats[sport]
                    # Остаток = План всех - Факт (положительное = остаток, отрицательное = перерасход)
                    ostatok_c = stats['plan_children'] - stats['fact_children']
                    ostatok_t = stats['plan_trainers'] - stats['fact_trainers']
                    
                    # Экономия/Перерасход = План - Факт ТОЛЬКО для проведённых/отменённых
                    # Положительное = экономия, отрицательное = перерасход
                    if stats['plan_children_completed'] > 0:
                        diff_c = stats['plan_children_completed'] - stats['fact_children']
                        diff_c_str = f"{diff_c:.2f}"
                    else:
                        diff_c_str = "н/д"  # Нет проведённых/отменённых мероприятий
                    
                    if stats['plan_trainers_completed'] > 0:
                        diff_t = stats['plan_trainers_completed'] - stats['fact_trainers']
                        diff_t_str = f"{diff_t:.2f}"
                    else:
                        diff_t_str = "н/д"  # Нет проведённых/отменённых мероприятий
                    
                    writer.writerow([
                        sport, stats['count'],
                        f"{stats['plan_children']:.2f}", f"{stats['fact_children']:.2f}", diff_c_str, f"{ostatok_c:.2f}",
                        f"{stats['plan_trainers']:.2f}", f"{stats['fact_trainers']:.2f}", diff_t_str, f"{ostatok_t:.2f}"
                    ])
            
            elif self.current_report_type == 'status':
                writer.writerow([
                    'Статус', 'Месяц', 'Вид спорта', 'Тип', 'Название', 'Место', 'Примечания'
                ])
                
                # Сортируем по статусу и месяцу
                for event in sorted(filtered_events, key=lambda e: (e.status or "Запланировано", MONTHS.index(e.month) if e.month in MONTHS else 999)):
                    writer.writerow([
                        event.status or 'Запланировано',
                        event.month,
                        event.sport,
                        event.event_type,
                        event.name,
                        event.location,
                        event.notes or ""
                    ])
            
            elif self.current_report_type == 'sports':
                writer.writerow([
                    'Вид спорта', 'Месяц', 'Тип', 'Название', 'Место', 'Статус',
                    'План: детей (₽)', 'План: тренеры (₽)'
                ])
                
                # Сортируем по спорту и месяцу
                for event in sorted(filtered_events, key=lambda e: (e.sport, MONTHS.index(e.month) if e.month in MONTHS else 999)):
                    writer.writerow([
                        event.sport,
                        event.month,
                        event.event_type,
                        event.name,
                        event.location,
                        event.status or 'Запланировано',
                        f"{event.children_budget:.2f}",
                        f"{event.trainers_budget:.2f}"
                    ])
            
            elif self.current_report_type == 'by_type':
                writer.writerow([
                    'Вид спорта', 'Тип мероприятия', 'Мероприятий',
                    'План: детей (₽)', 'Факт: детей (₽)', 'Отклонение детей',
                    'План: тренеры (₽)', 'Факт: тренеры (₽)', 'Отклонение тренеров'
                ])
                
                # Собираем статистику по видам спорта и типам
                sport_stats = {}
                for event in filtered_events:
                    if event.sport not in sport_stats:
                        sport_stats[event.sport] = {
                            'Внутреннее': {'count': 0, 'plan_children': 0, 'fact_children': 0, 'plan_trainers': 0, 'fact_trainers': 0, 'plan_children_completed': 0, 'plan_trainers_completed': 0},
                            'Выездное': {'count': 0, 'plan_children': 0, 'fact_children': 0, 'plan_trainers': 0, 'fact_trainers': 0, 'plan_children_completed': 0, 'plan_trainers_completed': 0}
                        }
                    
                    event_type = event.event_type
                    stats = sport_stats[event.sport][event_type]
                    stats['count'] += 1
                    stats['plan_children'] += event.children_budget
                    stats['plan_trainers'] += event.trainers_budget
                    
                    if event.status in ["Проведено", "Отменено"]:
                        stats['plan_children_completed'] += event.children_budget
                        stats['plan_trainers_completed'] += event.trainers_budget
                        
                        if event.status == "Проведено":
                            stats['fact_children'] += event.actual_children_budget if event.actual_children_budget else event.children_budget
                            stats['fact_trainers'] += event.actual_trainers_budget if event.actual_trainers_budget else event.trainers_budget
                
                # Выводим данные
                for sport in sorted(sport_stats.keys()):
                    for event_type in ['Внутреннее', 'Выездное']:
                        stats = sport_stats[sport][event_type]
                        if stats['count'] > 0:
                            diff_c = stats['plan_children_completed'] - stats['fact_children'] if stats['plan_children_completed'] > 0 else 0
                            diff_t = stats['plan_trainers_completed'] - stats['fact_trainers'] if stats['plan_trainers_completed'] > 0 else 0
                            
                            writer.writerow([
                                sport,
                                event_type,
                                stats['count'],
                                f"{stats['plan_children']:.2f}",
                                f"{stats['fact_children']:.2f}",
                                f"{diff_c:.2f}",
                                f"{stats['plan_trainers']:.2f}",
                                f"{stats['fact_trainers']:.2f}",
                                f"{diff_t:.2f}"
                            ])
            
            elif self.current_report_type == 'annual_ppo':
                writer.writerow([
                    '№', 'Тип', 'Название', 'Место', 'Месяц', 'Затраты (руб)', '1 кв.', '2 кв.', '3 кв.', '4 кв.',
                    'Категория расходов', 'Описание/Маршрут', 'Дни/Кол-во', 'Ставка', 'Человек', 'Сумма'
                ])
                
                # Определяем квартал
                q_map = {
                    'Январь': 1, 'Февраль': 1, 'Март': 1,
                    'Апрель': 2, 'Май': 2, 'Июнь': 2,
                    'Июль': 3, 'Август': 3, 'Сентябрь': 3,
                    'Октябрь': 4, 'Ноябрь': 4, 'Декабрь': 4
                }
                
                # Разделяем на выездные и внутренние
                away_events_csv = [e for e in filtered_events if e.event_type == "Выездное"]
                internal_events_csv = [e for e in filtered_events if e.event_type == "Внутреннее"]
                
                # 1. ВЫЕЗДНЫЕ МЕРОПРИЯТИЯ
                if away_events_csv:
                    # Заголовок секции
                    writer.writerow(['', '1. ВЫЕЗДНЫЕ МЕРОПРИЯТИЯ', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
                    
                    # Предварительный расчёт итогов
                    away_q_totals_csv = {1: 0, 2: 0, 3: 0, 4: 0}
                    away_total_csv = 0
                    for event in away_events_csv:
                        quarter = q_map.get(event.month, 1)
                        away_q_totals_csv[quarter] += event.children_budget
                        away_total_csv += event.children_budget
                    
                    # Итоговая строка
                    writer.writerow([
                        '', '', '', '', '', 
                        format_number_ru(away_total_csv),
                        format_number_ru(away_q_totals_csv[1]),
                        format_number_ru(away_q_totals_csv[2]),
                        format_number_ru(away_q_totals_csv[3]),
                        format_number_ru(away_q_totals_csv[4]),
                        '', '', '', '', '', ''
                    ])
                    
                    # Мероприятия
                    for idx, event in enumerate(away_events_csv, 1):
                        quarter = q_map.get(event.month, 1)
                        q_vals = ['', '', '', '']
                        q_vals[quarter-1] = format_number_ru(event.children_budget)
                        
                        # Получаем смету ППО
                        estimates = self.db.get_estimates_by_event(event.id)
                        ppo_estimate = None
                        for est in estimates:
                            if est[2] == 'ППО':
                                ppo_estimate = est
                                break
                        
                        # Строка мероприятия
                        writer.writerow([
                            f"1.{idx:03d}",
                            event.event_type,
                            event.name,
                            event.location,
                            event.month,
                            format_number_ru(event.children_budget),
                            q_vals[0], q_vals[1], q_vals[2], q_vals[3],
                            '', '', '', '', '', ''
                        ])
                        
                        # Детализация по смете
                        if ppo_estimate:
                            estimate_id = ppo_estimate[0]
                            items = self.db.get_estimate_items(estimate_id)
                            
                            for item in items:
                                category = item[2]
                                description = item[3] or ''
                                days_count = item[5] or 0
                                rate = item[6] or 0
                                people_count = item[4] or 0
                                total = item[7] or 0
                                
                                writer.writerow([
                                    '', '', '', '', '', '', '', '', '', '',
                                    category,
                                    description,
                                    days_count,
                                    format_number_ru(rate),
                                    people_count,
                                    format_number_ru(total)
                                ])
                
                # 2. ВНУТРЕННИЕ МЕРОПРИЯТИЯ
                if internal_events_csv:
                    # Заголовок секции
                    writer.writerow(['', '2. ВНУТРЕННИЕ И ГОРОДСКИЕ МЕРОПРИЯТИЯ', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
                    
                    # Предварительный расчёт итогов
                    internal_q_totals_csv = {1: 0, 2: 0, 3: 0, 4: 0}
                    internal_total_csv = 0
                    for event in internal_events_csv:
                        quarter = q_map.get(event.month, 1)
                        internal_q_totals_csv[quarter] += event.children_budget
                        internal_total_csv += event.children_budget
                    
                    # Итоговая строка
                    writer.writerow([
                        '', '', '', '', '',
                        format_number_ru(internal_total_csv),
                        format_number_ru(internal_q_totals_csv[1]),
                        format_number_ru(internal_q_totals_csv[2]),
                        format_number_ru(internal_q_totals_csv[3]),
                        format_number_ru(internal_q_totals_csv[4]),
                        '', '', '', '', '', ''
                    ])
                    
                    # Мероприятия
                    for idx, event in enumerate(internal_events_csv, 1):
                        quarter = q_map.get(event.month, 1)
                        q_vals = ['', '', '', '']
                        q_vals[quarter-1] = format_number_ru(event.children_budget)
                        
                        # Получаем смету ППО
                        estimates = self.db.get_estimates_by_event(event.id)
                        ppo_estimate = None
                        for est in estimates:
                            if est[2] == 'ППО':
                                ppo_estimate = est
                                break
                        
                        # Строка мероприятия
                        writer.writerow([
                            f"2.{idx:03d}",
                            event.event_type,
                            event.name,
                            event.location,
                            event.month,
                            format_number_ru(event.children_budget),
                            q_vals[0], q_vals[1], q_vals[2], q_vals[3],
                            '', '', '', '', '', ''
                        ])
                        
                        # Детализация по смете
                        if ppo_estimate:
                            estimate_id = ppo_estimate[0]
                            items = self.db.get_estimate_items(estimate_id)
                            
                            for item in items:
                                category = item[2]
                                description = item[3] or ''
                                days_count = item[5] or 0
                                rate = item[6] or 0
                                people_count = item[4] or 0
                                total = item[7] or 0
                                
                                writer.writerow([
                                    '', '', '', '', '', '', '', '', '', '',
                                    category,
                                    description,
                                    days_count,
                                    format_number_ru(rate),
                                    people_count,
                                    format_number_ru(total)
                                ])
            
            elif self.current_report_type == 'annual_uevp':
                writer.writerow([
                    'Должность', 'Месяц', 'Количество дней', 'Город', 'Цель командировки',
                    'Расходы на проезд, руб.', 'Расходы на проживание, руб.', 'Суточные, руб.',
                    'Итого расходов, руб.', 'Фактические расходы', 'Экономия/перерасход'
                ])
                
                for event in filtered_events:
                    # Получаем смету УЭВП для мероприятия
                    estimate_data = self.db.cursor.execute('''
                        SELECT id, total_amount
                        FROM estimates
                        WHERE event_id = ? AND estimate_type = 'УЭВП'
                    ''', (event.id,)).fetchone()
                    
                    if not estimate_data:
                        continue
                    
                    estimate_id = estimate_data[0]
                    
                    # Получаем детали сметы
                    items = self.db.cursor.execute('''
                        SELECT category, SUM(total) as total, MAX(days_count) as days
                        FROM estimate_items
                        WHERE estimate_id = ?
                        GROUP BY category
                    ''', (estimate_id,)).fetchall()
                    
                    proezd = 0
                    prozhivanie = 0
                    sutochnie = 0
                    days = 0
                    
                    for category, total, day_count in items:
                        if category == 'Проезд':
                            proezd = total
                        elif category == 'Проживание':
                            prozhivanie = total
                            days = day_count or days
                        elif category == 'Суточные':
                            sutochnie = total
                            days = day_count or days
                    
                    if days == 0:
                        days = 5
                    
                    # Формируем цель командировки
                    purpose = f"Сопровождение спортсменов для участия в {event.name} по виду спорта {event.sport}"
                    
                    # Итого по мероприятию
                    event_total = proezd + prozhivanie + sutochnie
                    
                    # Фактические расходы - только для проведённых и отменённых
                    fact_str = ""
                    economy_str = ""
                    if event.status in ["Проведено", "Отменено"]:
                        fact_amount = event.actual_trainers_budget if event.actual_trainers_budget is not None else event_total
                        fact_str = format_number_ru(fact_amount)
                        economy_amount = event_total - fact_amount
                        economy_str = format_number_ru(economy_amount)
                    
                    writer.writerow([
                        'Тренер',
                        event.month,
                        days,
                        event.location,
                        purpose,
                        format_number_ru(proezd),
                        format_number_ru(prozhivanie),
                        format_number_ru(sutochnie),
                        format_number_ru(event_total),
                        fact_str,
                        economy_str
                    ])
            
            else:  # 'full' и 'summary'
                writer.writerow([
                    'ID', 'Месяц', 'Тип', 'Вид спорта', 'Название', 'Место',
                    'План: детей (₽)', 'План: тренеры (₽)',
                    'Статус', 'Факт: даты', 'Факт: детей (₽)', 'Факт: тренеры (₽)',
                    'Причина отмены', 'Примечания'
                ])
                
                # Данные
                for event in filtered_events:
                    fact_dates = ""
                    if event.actual_start_date and event.actual_end_date:
                        fact_dates = f"{event.actual_start_date} - {event.actual_end_date}"
                    elif event.actual_start_date:
                        fact_dates = event.actual_start_date
                    
                    writer.writerow([
                        event.id,
                        event.month,
                        event.event_type,
                        event.sport,
                        event.name,
                        event.location,
                        format_number_ru(event.children_budget),
                        format_number_ru(event.trainers_budget),
                        event.status or 'Запланировано',
                        fact_dates,
                        format_number_ru(event.actual_children_budget) if event.actual_children_budget else "",
                        format_number_ru(event.actual_trainers_budget) if event.actual_trainers_budget else "",
                        event.cancellation_reason or "",
                        event.notes or ""
                    ])
    
    def _save_as_html(self, filename):
        """Сохранить отчёт как HTML"""
        events_data = self.db.get_events_by_year(self.year)
        events = [Event.from_db_row(row) for row in events_data]
        
        # Определяем заголовок в зависимости от типа отчета
        report_titles = {
            'full': 'Календарный план',
            'financial': 'Финансовый отчёт',
            'sports': 'Отчёт по видам спорта',
            'status': 'Отчёт по статусам',
            'summary': 'Краткая сводка',
            'by_type': 'Финансовый отчёт по типам мероприятий',
            'annual_ppo': 'Годовой отчет ППО',
            'annual_uevp': 'Годовой отчет УЭВП'
        }
        
        title = report_titles.get(self.current_report_type, 'Календарный план')
        
        # Стили для печати
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title} {self.year}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background: #fff;
        }}
        h1 {{
            color: #0066B3;
            text-align: center;
        }}
        h2 {{
            color: #004B87;
            border-bottom: 2px solid #0066B3;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #0066B3;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .status-completed {{
            background-color: #d4edda;
        }}
        .status-cancelled {{
            background-color: #f8d7da;
        }}
        .status-postponed {{
            background-color: #fff3cd;
        }}
        .summary {{
            background: #f5f7fa;
            padding: 15px;
            border-left: 4px solid #0066B3;
            margin: 20px 0;
        }}
        @media print {{
            body {{ margin: 0; }}
            h1 {{ page-break-after: avoid; }}
            table {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <h1>{title} на {self.year} год</h1>
    <h2>ДЮСК Ямбург</h2>
"""
        
        # Генерируем контент в зависимости от типа отчета
        if self.current_report_type == 'financial':
            # Финансовый отчет
            html_content += """
    <table>
        <thead>
            <tr>
                <th>Вид спорта</th>
                <th>Мероприятий</th>
                <th>План: детей (₽)</th>
                <th>Факт: детей (₽)</th>
                <th>Экономия/Перерасход ППО</th>
                <th>Остаток ППО</th>
                <th>План: тренеры (₽)</th>
                <th>Факт: тренеры (₽)</th>
                <th>Экономия/Перерасход УЭВП</th>
                <th>Остаток УЭВП</th>
            </tr>
        </thead>
        <tbody>
"""
            
            # Группируем по видам спорта
            sport_stats = {}
            for event in events:
                if event.sport not in sport_stats:
                    sport_stats[event.sport] = {
                        'count': 0, 
                        'plan_children': 0, 'fact_children': 0,
                        'plan_trainers': 0, 'fact_trainers': 0,
                        'plan_children_completed': 0,  # План только для проведённых/отменённых
                        'plan_trainers_completed': 0   # План только для проведённых/отменённых
                    }
                
                sport_stats[event.sport]['count'] += 1
                sport_stats[event.sport]['plan_children'] += event.children_budget
                sport_stats[event.sport]['plan_trainers'] += event.trainers_budget
                
                # Факт и план для проведённых/отменённых (для расчёта экономии/перерасхода)
                if event.status in ["Проведено", "Отменено"]:
                    sport_stats[event.sport]['plan_children_completed'] += event.children_budget
                    sport_stats[event.sport]['plan_trainers_completed'] += event.trainers_budget
                    
                    if event.status == "Проведено":
                        if event.actual_children_budget is not None:
                            sport_stats[event.sport]['fact_children'] += event.actual_children_budget
                        else:
                            # Если мероприятие проведено, но факт не указан - берём план
                            sport_stats[event.sport]['fact_children'] += event.children_budget
                        
                        if event.actual_trainers_budget is not None:
                            sport_stats[event.sport]['fact_trainers'] += event.actual_trainers_budget
                        else:
                            # Если мероприятие проведено, но факт не указан - берём план
                            sport_stats[event.sport]['fact_trainers'] += event.trainers_budget
                    # Для отменённых факт = 0 (не тратили)
                # Для запланированных, перенесённых - факт = 0
            
            for sport in sorted(sport_stats.keys()):
                stats = sport_stats[sport]
                # Остаток = План всех - Факт (положительное = остаток, отрицательное = перерасход)
                ostatok_c = stats['plan_children'] - stats['fact_children']
                ostatok_t = stats['plan_trainers'] - stats['fact_trainers']
                
                # Экономия/Перерасход = План - Факт ТОЛЬКО для проведённых/отменённых
                # Положительное = экономия (зелёный), отрицательное = перерасход (красный)
                if stats['plan_children_completed'] > 0:
                    diff_c = stats['plan_children_completed'] - stats['fact_children']
                    diff_c_html = f"<td style=\"color: {'green' if diff_c > 0 else 'red' if diff_c < 0 else 'black'};\">{diff_c:+.2f}</td>"
                else:
                    diff_c_html = "<td style=\"color: gray; font-style: italic;\">н/д</td>"
                
                if stats['plan_trainers_completed'] > 0:
                    diff_t = stats['plan_trainers_completed'] - stats['fact_trainers']
                    diff_t_html = f"<td style=\"color: {'green' if diff_t > 0 else 'red' if diff_t < 0 else 'black'};\">{diff_t:+.2f}</td>"
                else:
                    diff_t_html = "<td style=\"color: gray; font-style: italic;\">н/д</td>"
                
                html_content += f"""
            <tr>
                <td>{html.escape(sport)}</td>
                <td>{stats['count']}</td>
                <td>{stats['plan_children']:.2f}</td>
                <td>{stats['fact_children']:.2f}</td>
                {diff_c_html}
                <td style="color: {'green' if ostatok_c > 0 else 'red' if ostatok_c < 0 else 'black'}; font-weight: bold;">{ostatok_c:+.2f}</td>
                <td>{stats['plan_trainers']:.2f}</td>
                <td>{stats['fact_trainers']:.2f}</td>
                {diff_t_html}
                <td style="color: {'green' if ostatok_t > 0 else 'red' if ostatok_t < 0 else 'black'}; font-weight: bold;">{ostatok_t:+.2f}</td>
            </tr>
"""
        
        elif self.current_report_type == 'status':
            # Отчет по статусам
            html_content += """
    <table>
        <thead>
            <tr>
                <th>Статус</th>
                <th>Месяц</th>
                <th>Вид спорта</th>
                <th>Тип</th>
                <th>Название</th>
                <th>Место</th>
            </tr>
        </thead>
        <tbody>
"""
            
            # Сортируем по статусу и месяцу
            for event in sorted(events, key=lambda e: (e.status or "Запланировано", MONTHS.index(e.month) if e.month in MONTHS else 999)):
                status_class = ""
                if event.status == "Проведено":
                    status_class = "status-completed"
                elif event.status == "Отменено":
                    status_class = "status-cancelled"
                elif event.status == "Перенесено":
                    status_class = "status-postponed"
                
                html_content += f"""
            <tr class="{status_class}">
                <td>{html.escape(event.status or 'Запланировано')}</td>
                <td>{html.escape(event.month)}</td>
                <td>{html.escape(event.sport)}</td>
                <td>{html.escape(event.event_type)}</td>
                <td>{html.escape(event.name)}</td>
                <td>{html.escape(event.location)}</td>
            </tr>
"""
        
        elif self.current_report_type == 'sports':
            # Отчет по видам спорта
            html_content += """
    <table>
        <thead>
            <tr>
                <th>Вид спорта</th>
                <th>Месяц</th>
                <th>Тип</th>
                <th>Название</th>
                <th>Место</th>
                <th>Статус</th>
                <th>План: детей (₽)</th>
                <th>План: тренеры (₽)</th>
            </tr>
        </thead>
        <tbody>
"""
            
            # Сортируем по спорту и месяцу
            for event in sorted(events, key=lambda e: (e.sport, MONTHS.index(e.month) if e.month in MONTHS else 999)):
                status_class = ""
                if event.status == "Проведено":
                    status_class = "status-completed"
                elif event.status == "Отменено":
                    status_class = "status-cancelled"
                elif event.status == "Перенесено":
                    status_class = "status-postponed"
                
                html_content += f"""
            <tr class="{status_class}">
                <td>{html.escape(event.sport)}</td>
                <td>{html.escape(event.month)}</td>
                <td>{html.escape(event.event_type)}</td>
                <td>{html.escape(event.name)}</td>
                <td>{html.escape(event.location)}</td>
                <td>{html.escape(event.status or 'Запланировано')}</td>
                <td>{event.children_budget:.2f}</td>
                <td>{event.trainers_budget:.2f}</td>
            </tr>
"""
        
        elif self.current_report_type == 'by_type':
            # Отчет по типам мероприятий
            html_content += """
    <table>
        <thead>
            <tr>
                <th>Вид спорта</th>
                <th>Тип мероприятия</th>
                <th>Мероприятий</th>
                <th>План: детей (₽)</th>
                <th>Факт: детей (₽)</th>
                <th>Отклонение детей</th>
                <th>План: тренеры (₽)</th>
                <th>Факт: тренеры (₽)</th>
                <th>Отклонение тренеров</th>
            </tr>
        </thead>
        <tbody>
"""
            
            # Собираем статистику по видам спорта и типам
            sport_stats = {}
            for event in events:
                if event.sport not in sport_stats:
                    sport_stats[event.sport] = {
                        'Внутреннее': {'count': 0, 'plan_children': 0, 'fact_children': 0, 'plan_trainers': 0, 'fact_trainers': 0, 'plan_children_completed': 0, 'plan_trainers_completed': 0},
                        'Выездное': {'count': 0, 'plan_children': 0, 'fact_children': 0, 'plan_trainers': 0, 'fact_trainers': 0, 'plan_children_completed': 0, 'plan_trainers_completed': 0}
                    }
                
                event_type = event.event_type
                stats = sport_stats[event.sport][event_type]
                stats['count'] += 1
                stats['plan_children'] += event.children_budget
                stats['plan_trainers'] += event.trainers_budget
                
                if event.status in ["Проведено", "Отменено"]:
                    stats['plan_children_completed'] += event.children_budget
                    stats['plan_trainers_completed'] += event.trainers_budget
                    
                    if event.status == "Проведено":
                        stats['fact_children'] += event.actual_children_budget if event.actual_children_budget else event.children_budget
                        stats['fact_trainers'] += event.actual_trainers_budget if event.actual_trainers_budget else event.trainers_budget
            
            # Выводим данные
            for sport in sorted(sport_stats.keys()):
                for event_type in ['Внутреннее', 'Выездное']:
                    stats = sport_stats[sport][event_type]
                    if stats['count'] > 0:
                        diff_c = stats['plan_children_completed'] - stats['fact_children'] if stats['plan_children_completed'] > 0 else 0
                        diff_t = stats['plan_trainers_completed'] - stats['fact_trainers'] if stats['plan_trainers_completed'] > 0 else 0
                        
                        html_content += f"""
            <tr>
                <td>{html.escape(sport)}</td>
                <td>{html.escape(event_type)}</td>
                <td>{stats['count']}</td>
                <td>{stats['plan_children']:.2f}</td>
                <td>{stats['fact_children']:.2f}</td>
                <td style="color: {'green' if diff_c > 0 else 'red' if diff_c < 0 else 'black'}; font-weight: bold;">{diff_c:+.2f}</td>
                <td>{stats['plan_trainers']:.2f}</td>
                <td>{stats['fact_trainers']:.2f}</td>
                <td style="color: {'green' if diff_t > 0 else 'red' if diff_t < 0 else 'black'}; font-weight: bold;">{diff_t:+.2f}</td>
            </tr>
"""
        
        elif self.current_report_type == 'summary':
            # Краткая сводка - только статистика, без детального списка
            total = len(events)
            internal = sum(1 for e in events if e.event_type == "Внутреннее")
            external = sum(1 for e in events if e.event_type == "Выездное")
            conducted = sum(1 for e in events if e.status == "Проведено")
            cancelled = sum(1 for e in events if e.status == "Отменено")
            postponed = sum(1 for e in events if e.status == "Перенесено")
            planned = sum(1 for e in events if e.status == "Запланировано")
            
            html_content += f"""
    <div class="summary">
        <h3>ОБЩАЯ СТАТИСТИКА</h3>
        <p><strong>Всего мероприятий:</strong> {total}</p>
        <p style="margin-left: 20px;">Внутренних: {internal} ({internal/total*100:.1f}%)</p>
        <p style="margin-left: 20px;">Выездных: {external} ({external/total*100:.1f}%)</p>
        
        <h4 style="margin-top: 20px;">По статусам:</h4>
        <p style="margin-left: 20px;">Проведено: {conducted} ({conducted/total*100:.1f}%)</p>
"""
            if cancelled > 0:
                html_content += f"""        <p style="margin-left: 20px;">Отменено: {cancelled} ({cancelled/total*100:.1f}%)</p>
"""
            if postponed > 0:
                html_content += f"""        <p style="margin-left: 20px;">Перенесено: {postponed} ({postponed/total*100:.1f}%)</p>
"""
            html_content += f"""        <p style="margin-left: 20px;">Запланировано: {planned} ({planned/total*100:.1f}%)</p>
    </div>
    
    <h3 style="margin-top: 30px;">ПО ВИДАМ СПОРТА</h3>
    <table>
        <thead>
            <tr>
                <th>Вид спорта</th>
                <th>Количество</th>
                <th>Процент от общего</th>
            </tr>
        </thead>
        <tbody>
"""
            
            # Статистика по видам спорта
            sport_counts = {}
            for event in events:
                sport_counts[event.sport] = sport_counts.get(event.sport, 0) + 1
            
            for sport in sorted(sport_counts.keys()):
                count = sport_counts[sport]
                html_content += f"""
            <tr>
                <td>{html.escape(sport)}</td>
                <td>{count}</td>
                <td>{count/total*100:.1f}%</td>
            </tr>
"""
            
            html_content += """
        </tbody>
    </table>
"""
        
        elif self.current_report_type == 'annual_ppo':
            # Годовой отчет ППО с разбивкой по кварталам и детализацией смет
            html_content += """
    <table style="font-size: 11px;">
        <thead>
            <tr>
                <th>№</th>
                <th>Наименование статей затрат/Мероприятий</th>
                <th>Место/Ед.изм.</th>
                <th>Даты/Кол-во</th>
                <th>Стоим.</th>
                <th>Чел.</th>
                <th>Затраты (руб)</th>
                <th>1 кв.</th>
                <th>2 кв.</th>
                <th>3 кв.</th>
                <th>4 кв.</th>
            </tr>
        </thead>
        <tbody>
"""
            
            q_map = {
                'Январь': 1, 'Февраль': 1, 'Март': 1,
                'Апрель': 2, 'Май': 2, 'Июнь': 2,
                'Июль': 3, 'Август': 3, 'Сентябрь': 3,
                'Октябрь': 4, 'Ноябрь': 4, 'Декабрь': 4
            }
            
            # Разделяем на выездные и внутренние
            away_events = [e for e in events if e.event_type == "Выездное"]
            internal_events = [e for e in events if e.event_type == "Внутреннее"]
            
            # Выездные мероприятия с детализацией
            if away_events:
                html_content += """
            <tr style="background-color: #e6f3ff;">
                <td colspan="11"><strong>1. ВЫЕЗДНЫЕ МЕРОПРИЯТИЯ</strong></td>
            </tr>
"""
                
                # Предварительный расчёт итогов по выездным для синей строки
                away_q_totals_html = {1: 0, 2: 0, 3: 0, 4: 0}
                away_total_html = 0
                for event in away_events:
                    quarter = q_map.get(event.month, 1)
                    away_q_totals_html[quarter] += event.children_budget
                    away_total_html += event.children_budget
                
                # Синяя итоговая строка с суммами по кварталам
                html_content += f"""
            <tr style="background-color: #0066B3; color: white; font-weight: bold;">
                <td colspan="6"></td>
                <td>{format_number_ru(away_total_html)}</td>
                <td>{format_number_ru(away_q_totals_html[1])}</td>
                <td>{format_number_ru(away_q_totals_html[2])}</td>
                <td>{format_number_ru(away_q_totals_html[3])}</td>
                <td>{format_number_ru(away_q_totals_html[4])}</td>
            </tr>
"""
                
                for idx, event in enumerate(away_events, 1):
                    quarter = q_map.get(event.month, 1)
                    
                    # Получаем смету ППО
                    estimates = self.db.get_estimates_by_event(event.id)
                    ppo_estimate = None
                    for est in estimates:
                        if est[2] == 'ППО':  # estimate_type
                            ppo_estimate = est
                            break
                    
                    # Заполняем кварталы
                    q_vals = ['', '', '', '']
                    q_vals[quarter-1] = format_number_ru(event.children_budget)
                    
                    # Название мероприятия (с трёхзначной нумерацией: 1.001, 1.002, и т.д.)
                    html_content += f"""
            <tr style="font-weight: bold;">
                <td>1.{idx:03d}</td>
                <td>{html.escape(event.name[:60])}</td>
                <td>{html.escape(event.location)}</td>
                <td>{html.escape(event.month)}</td>
                <td></td>
                <td></td>
                <td>{format_number_ru(event.children_budget)}</td>
                <td>{q_vals[0]}</td>
                <td>{q_vals[1]}</td>
                <td>{q_vals[2]}</td>
                <td>{q_vals[3]}</td>
            </tr>
"""
                    
                    # Детализация по смете
                    if ppo_estimate:
                        estimate_id = ppo_estimate[0]
                        items = self.db.get_estimate_items(estimate_id)
                        
                        for item in items:
                            category = item[2]
                            description = item[3] or ''
                            people_count = item[4] or 0
                            days_count = item[5] or 0
                            rate = item[6] or 0
                            
                            # Форматируем вывод
                            if category == "Проезд":
                                html_content += f"""
            <tr>
                <td></td>
                <td style="padding-left: 30px;">{category}</td>
                <td>{html.escape(description)}</td>
                <td>{days_count}</td>
                <td>{rate:.0f}</td>
                <td>{people_count}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
"""
                            elif category == "Проживание":
                                html_content += f"""
            <tr>
                <td></td>
                <td style="padding-left: 30px;">{category}</td>
                <td>дн</td>
                <td>{days_count}</td>
                <td>{rate:.0f}</td>
                <td>{people_count}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
"""
                            elif category == "Суточные":
                                html_content += f"""
            <tr>
                <td></td>
                <td style="padding-left: 30px;">{category}</td>
                <td>дн</td>
                <td>{days_count}</td>
                <td>{rate:.0f}</td>
                <td>{people_count}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
"""
            
            # Внутренние мероприятия
            if internal_events:
                html_content += """
            <tr style="background-color: #e6f3ff;">
                <td colspan="11"><strong>2. ВНУТРЕННИЕ И ГОРОДСКИЕ МЕРОПРИЯТИЯ</strong></td>
            </tr>
"""
                
                # Предварительный расчёт итогов по внутренним для синей строки
                internal_q_totals_html = {1: 0, 2: 0, 3: 0, 4: 0}
                internal_total_html = 0
                for event in internal_events:
                    quarter = q_map.get(event.month, 1)
                    internal_q_totals_html[quarter] += event.children_budget
                    internal_total_html += event.children_budget
                
                # Синяя итоговая строка с суммами по кварталам
                html_content += f"""
            <tr style="background-color: #0066B3; color: white; font-weight: bold;">
                <td colspan="6"></td>
                <td>{format_number_ru(internal_total_html)}</td>
                <td>{format_number_ru(internal_q_totals_html[1])}</td>
                <td>{format_number_ru(internal_q_totals_html[2])}</td>
                <td>{format_number_ru(internal_q_totals_html[3])}</td>
                <td>{format_number_ru(internal_q_totals_html[4])}</td>
            </tr>
"""
                
                for idx, event in enumerate(internal_events, 1):
                    quarter = q_map.get(event.month, 1)
                    
                    # Получаем смету ППО
                    estimates = self.db.get_estimates_by_event(event.id)
                    ppo_estimate = None
                    for est in estimates:
                        if est[2] == 'ППО':  # estimate_type
                            ppo_estimate = est
                            break
                    
                    # Заполняем кварталы
                    q_vals = ['', '', '', '']
                    q_vals[quarter-1] = format_number_ru(event.children_budget)
                    
                    # Название мероприятия (с трёхзначной нумерацией: 2.001, 2.002, и т.д.)
                    html_content += f"""
            <tr style="font-weight: bold;">
                <td>2.{idx:03d}</td>
                <td>{html.escape(event.name[:60])}</td>
                <td>{html.escape(event.location)}</td>
                <td>{html.escape(event.month)}</td>
                <td></td>
                <td></td>
                <td>{format_number_ru(event.children_budget)}</td>
                <td>{q_vals[0]}</td>
                <td>{q_vals[1]}</td>
                <td>{q_vals[2]}</td>
                <td>{q_vals[3]}</td>
            </tr>
"""
                    
                    # Детализация по смете
                    if ppo_estimate:
                        estimate_id = ppo_estimate[0]
                        items = self.db.get_estimate_items(estimate_id)
                        
                        for item in items:
                            category = item[2]
                            description = item[3] or ''
                            people_count = item[4] or 0
                            days_count = item[5] or 0
                            rate = item[6] or 0
                            
                            # Форматируем вывод - для внутренних выводим категорию и описание
                            html_content += f"""
            <tr>
                <td></td>
                <td style="padding-left: 30px;">{category}</td>
                <td>{html.escape(description)}</td>
                <td>{days_count}</td>
                <td>{rate:.0f}</td>
                <td>{people_count}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
"""
            
            html_content += """
        </tbody>
    </table>
"""
        
        elif self.current_report_type == 'annual_uevp':
            # Годовой отчет УЭВП - только выездные
            away_events = [e for e in events if e.event_type == "Выездное"]
            
            html_content += """
    <table>
        <thead>
            <tr>
                <th>Должность</th>
                <th>Месяц</th>
                <th>Дни</th>
                <th>Город</th>
                <th>Цель командировки</th>
                <th>Проезд (₽)</th>
                <th>Проживание (₽)</th>
                <th>Суточные (₽)</th>
                <th>Итого (₽)</th>
                <th>Факт (₽)</th>
                <th>Эк/Пер (₽)</th>
            </tr>
        </thead>
        <tbody>
"""
            
            total_proezd = 0
            total_prozhivanie = 0
            total_sutochnie = 0
            total_all = 0
            total_fact = 0
            
            for event in away_events:
                # Получаем смету УЭВП для этого мероприятия
                estimate_data = self.db.cursor.execute('''
                    SELECT id, total_amount
                    FROM estimates
                    WHERE event_id = ? AND estimate_type = 'УЭВП'
                ''', (event.id,)).fetchone()
                
                if not estimate_data:
                    continue
                
                estimate_id = estimate_data[0]
                
                # Получаем детали сметы
                items = self.db.cursor.execute('''
                    SELECT category, SUM(total) as total, MAX(days_count) as days
                    FROM estimate_items
                    WHERE estimate_id = ?
                    GROUP BY category
                ''', (estimate_id,)).fetchall()
                
                proezd = 0
                prozhivanie = 0
                sutochnie = 0
                days = 0
                
                for category, total, day_count in items:
                    if category == 'Проезд':
                        proezd = total
                    elif category == 'Проживание':
                        prozhivanie = total
                        days = day_count or days
                    elif category == 'Суточные':
                        sutochnie = total
                        days = day_count or days
                
                if days == 0:
                    days = 5
                
                # Формируем цель командировки
                purpose = f"Сопровождение спортсменов для участия в {event.name} по виду спорта {event.sport}"
                
                # Итого по мероприятию
                event_total = proezd + prozhivanie + sutochnie
                
                # Фактические расходы - только для проведённых и отменённых
                fact_cell = "-"
                economy_cell = "-"
                if event.status in ["Проведено", "Отменено"]:
                    fact_amount = event.actual_trainers_budget if event.actual_trainers_budget is not None else event_total
                    fact_cell = format_number_ru(fact_amount)
                    economy_amount = event_total - fact_amount
                    economy_cell = format_number_ru(economy_amount)
                    total_fact += fact_amount
                
                html_content += f"""
            <tr>
                <td>Тренер</td>
                <td>{html.escape(event.month)}</td>
                <td>{days}</td>
                <td>{html.escape(event.location)}</td>
                <td>{html.escape(purpose)}</td>
                <td>{format_number_ru(proezd)}</td>
                <td>{format_number_ru(prozhivanie)}</td>
                <td>{format_number_ru(sutochnie)}</td>
                <td>{format_number_ru(event_total)}</td>
                <td>{fact_cell}</td>
                <td>{economy_cell}</td>
            </tr>
"""
                
                total_proezd += proezd
                total_prozhivanie += prozhivanie
                total_sutochnie += sutochnie
                total_all += event_total
            
            # Строка итого
            total_fact_cell = format_number_ru(total_fact) if total_fact > 0 else "-"
            total_economy_cell = format_number_ru(total_all - total_fact) if total_fact > 0 else "-"
            
            html_content += f"""
            <tr style="font-weight: bold; background-color: #f0f0f0;">
                <td>ИТОГО:</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td>{format_number_ru(total_proezd)}</td>
                <td>{format_number_ru(total_prozhivanie)}</td>
                <td>{format_number_ru(total_sutochnie)}</td>
                <td>{format_number_ru(total_all)}</td>
                <td>{total_fact_cell}</td>
                <td>{total_economy_cell}</td>
            </tr>
        </tbody>
    </table>
"""
        
        else:  # 'full' and others
            html_content += """
    <table>
        <thead>
            <tr>
                <th>Месяц</th>
                <th>Тип</th>
                <th>Спорт</th>
                <th>Название</th>
                <th>Место</th>
                <th>Детей (₽)</th>
                <th>Тренеры (₽)</th>
                <th>Статус</th>
            </tr>
        </thead>
        <tbody>
"""
            
            for event in events:
                status_class = ""
                if event.status == "Проведено":
                    status_class = "status-completed"
                elif event.status == "Отменено":
                    status_class = "status-cancelled"
                elif event.status == "Перенесено":
                    status_class = "status-postponed"
                
                html_content += f"""
            <tr class="{status_class}">
                <td>{html.escape(event.month)}</td>
                <td>{html.escape(event.event_type)}</td>
                <td>{html.escape(event.sport)}</td>
                <td>{html.escape(event.name)}</td>
                <td>{html.escape(event.location)}</td>
                <td>{event.children_budget:.2f}</td>
                <td>{event.trainers_budget:.2f}</td>
                <td>{html.escape(event.status or 'Запланировано')}</td>
            </tr>
"""
            
            html_content += """
        </tbody>
    </table>
"""
        
        # Итоги (для всех, кроме summary - у него свои итоги уже встроены)
        if self.current_report_type != 'summary':
            # Для годового отчета УЭВП используем только выездные события
            events_for_totals = [e for e in events if e.event_type == "Выездное"] if self.current_report_type == 'annual_uevp' else events
            
            total_children_plan = sum(e.children_budget for e in events_for_totals)
            total_trainers_plan = sum(e.trainers_budget for e in events_for_totals)
            
            # Для финансового отчёта показываем план, факт и остаток
            if self.current_report_type == 'financial':
                total_children_fact = sum(
                    e.actual_children_budget if e.actual_children_budget is not None and e.status == "Проведено" 
                    else (e.children_budget if e.status == "Проведено" else 0) 
                    for e in events
                )
                total_trainers_fact = sum(
                    e.actual_trainers_budget if e.actual_trainers_budget is not None and e.status == "Проведено" 
                    else (e.trainers_budget if e.status == "Проведено" else 0) 
                    for e in events
                )
                
                ostatok_children = total_children_plan - total_children_fact
                ostatok_trainers = total_trainers_plan - total_trainers_fact
                
                html_content += f"""
    <div class="summary">
        <h3>ИТОГИ</h3>
        <p><strong>Всего мероприятий:</strong> {len(events)}</p>
        
        <h4 style="margin-top: 20px;">Бюджет на детей (ППО "Газпром добыча Ямбург профсоюз")</h4>
        <p style="margin-left: 20px;">План: {format_rubles(total_children_plan)}</p>
        <p style="margin-left: 20px;">Факт: {format_rubles(total_children_fact)}</p>
        <p style="margin-left: 20px; color: {'green' if ostatok_children > 0 else 'red' if ostatok_children < 0 else 'black'}; font-weight: bold;">
            Остаток: {format_rubles(abs(ostatok_children))} 
            ({'экономия' if ostatok_children > 0 else 'перерасход' if ostatok_children < 0 else 'по плану'})
        </p>
        
        <h4 style="margin-top: 20px;">Бюджет на тренеров (ф. УЭВП ООО "Газпром добыча Ямбург")</h4>
        <p style="margin-left: 20px;">План: {format_rubles(total_trainers_plan)}</p>
        <p style="margin-left: 20px;">Факт: {format_rubles(total_trainers_fact)}</p>
        <p style="margin-left: 20px; color: {'green' if ostatok_trainers > 0 else 'red' if ostatok_trainers < 0 else 'black'}; font-weight: bold;">
            Остаток: {format_rubles(abs(ostatok_trainers))} 
            ({'экономия' if ostatok_trainers > 0 else 'перерасход' if ostatok_trainers < 0 else 'по плану'})
        </p>
    </div>
"""
            elif self.current_report_type == 'annual_ppo':
                # Для годового отчета ППО - только ППО
                html_content += f"""
    <div class="summary">
        <h3>Итоги</h3>
        <p><strong>Всего мероприятий:</strong> {len(events_for_totals)}</p>
        <p><strong>Бюджет на детей (ППО "Газпром добыча Ямбург профсоюз"):</strong> {format_rubles(total_children_plan)}</p>
    </div>
"""
            elif self.current_report_type == 'annual_uevp':
                # Для годового отчета УЭВП - только УЭВП
                html_content += f"""
    <div class="summary">
        <h3>Итоги</h3>
        <p><strong>Всего выездных мероприятий:</strong> {len(events_for_totals)}</p>
        <p><strong>Бюджет на тренеров (ф. УЭВП ООО "Газпром добыча Ямбург"):</strong> {format_rubles(total_trainers_plan)}</p>
    </div>
"""
            else:
                # Для остальных отчётов - простые итоги
                html_content += f"""
    <div class="summary">
        <h3>Итоги</h3>
        <p><strong>Всего мероприятий:</strong> {len(events)}</p>
        <p><strong>Бюджет на детей (ППО "Газпром добыча Ямбург профсоюз"):</strong> {format_rubles(total_children_plan)}</p>
        <p><strong>Бюджет на тренеров (ф. УЭВП ООО "Газпром добыча Ямбург"):</strong> {format_rubles(total_trainers_plan)}</p>
    </div>
"""
        else:
            # Для summary добавляем финансовую сводку
            plan_children = sum(e.children_budget for e in events)
            plan_trainers = sum(e.trainers_budget for e in events)
            
            # План для проведённых/отменённых (для расчёта экономии/перерасхода)
            plan_children_completed = sum(e.children_budget for e in events if e.status in ["Проведено", "Отменено"])
            plan_trainers_completed = sum(e.trainers_budget for e in events if e.status in ["Проведено", "Отменено"])
            
            # Факт только для проведённых
            fact_children = sum(
                e.actual_children_budget if e.actual_children_budget is not None else e.children_budget
                for e in events if e.status == "Проведено"
            )
            fact_trainers = sum(
                e.actual_trainers_budget if e.actual_trainers_budget is not None else e.trainers_budget
                for e in events if e.status == "Проведено"
            )
            
            html_content += f"""
    <h3 style="margin-top: 30px;">ФИНАНСОВАЯ СВОДКА</h3>
    <div class="summary">
        <h4>Бюджет на детей (ППО "Газпром добыча Ямбург профсоюз")</h4>
        <p>План: {format_rubles(plan_children)}</p>
        <p>Факт: {format_rubles(fact_children)}</p>
"""
            # Экономия/Перерасход только для проведённых/отменённых
            if plan_children_completed > 0:
                diff_c = plan_children_completed - fact_children
                html_content += f"""        <p style="color: {'green' if diff_c > 0 else 'red' if diff_c < 0 else 'black'}; font-weight: bold;">
            {'✓ Экономия' if diff_c > 0 else '⚠ Перерасход' if diff_c < 0 else '✓ По плану'}: 
            {format_rubles(abs(diff_c)) if diff_c != 0 else ''}
            {f' ({abs(diff_c)/plan_children_completed*100:.1f}%)' if diff_c != 0 else ''}
        </p>
"""
            else:
                html_content += """        <p style="color: gray; font-style: italic;">(н/д - нет проведённых/отменённых)</p>
"""
            
            html_content += f"""        
        <h4 style="margin-top: 20px;">Бюджет на тренеров (ф. УЭВП ООО "Газпром добыча Ямбург")</h4>
        <p>План: {format_rubles(plan_trainers)}</p>
        <p>Факт: {format_rubles(fact_trainers)}</p>
"""
            # Экономия/Перерасход только для проведённых/отменённых
            if plan_trainers_completed > 0:
                diff_t = plan_trainers_completed - fact_trainers
                html_content += f"""        <p style="color: {'green' if diff_t > 0 else 'red' if diff_t < 0 else 'black'}; font-weight: bold;">
            {'✓ Экономия' if diff_t > 0 else '⚠ Перерасход' if diff_t < 0 else '✓ По плану'}: 
            {format_rubles(abs(diff_t)) if diff_t != 0 else ''}
            {f' ({abs(diff_t)/plan_trainers_completed*100:.1f}%)' if diff_t != 0 else ''}
        </p>
"""
            else:
                html_content += """        <p style="color: gray; font-style: italic;">(н/д - нет проведённых/отменённых)</p>
"""
            
            html_content += """    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

