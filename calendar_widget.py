# -*- coding: utf-8 -*-
"""
Простой виджет календаря на чистом tkinter (без внешних библиотек)
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar


class CalendarDialog:
    """Диалоговое окно с календарём для выбора даты"""
    
    def __init__(self, parent, initial_date=None):
        """
        Инициализация календаря
        
        Args:
            parent: Родительское окно
            initial_date: Начальная дата (datetime или None)
        """
        self.parent = parent
        self.selected_date = initial_date if initial_date else datetime.now()
        self.result = None
        
        # Создаем модальное окно
        self.window = tk.Toplevel(parent)
        self.window.title("Выбор даты")
        self.window.geometry("700x350")  # Увеличили ширину для отображения всех 7 дней
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Центрируем окно
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.window.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._update_calendar()
    
    def _create_widgets(self):
        """Создать виджеты календаря"""
        # Фрейм для навигации
        nav_frame = tk.Frame(self.window)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопка "Предыдущий месяц"
        self.prev_btn = tk.Button(
            nav_frame, text="◄", width=3,
            command=self._prev_month
        )
        self.prev_btn.pack(side=tk.LEFT)
        
        # Метка с месяцем и годом
        self.month_label = tk.Label(
            nav_frame, text="", 
            font=('Arial', 12, 'bold')
        )
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        # Кнопка "Следующий месяц"
        self.next_btn = tk.Button(
            nav_frame, text="►", width=3,
            command=self._next_month
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        # Фрейм для календарной сетки
        cal_frame = tk.Frame(self.window)
        cal_frame.pack(padx=10, pady=5)
        
        # Заголовки дней недели
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for col, day in enumerate(days):
            tk.Label(
                cal_frame, text=day, 
                font=('Arial', 9, 'bold'),
                width=5
            ).grid(row=0, column=col, padx=2, pady=1)
        
        # Создаем кнопки для дней (6 недель x 7 дней)
        self.day_buttons = []
        for row in range(6):
            week = []
            for col in range(7):
                btn = tk.Button(
                    cal_frame, text="", width=5,
                    command=lambda r=row, c=col: self._select_day(r, c)
                )
                btn.grid(row=row+1, column=col, padx=2, pady=1)
                week.append(btn)
            self.day_buttons.append(week)
        
        # Кнопки действий
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame, text="Сегодня", width=10,
            command=self._select_today
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="Очистить", width=10,
            command=self._clear_date
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="Отмена", width=10,
            command=self._cancel
        ).pack(side=tk.LEFT, padx=5)
    
    def _update_calendar(self):
        """Обновить отображение календаря"""
        year = self.selected_date.year
        month = self.selected_date.month
        
        # Обновляем заголовок
        month_names = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        self.month_label.config(text=f"{month_names[month-1]} {year}")
        
        # Получаем календарь месяца
        cal = calendar.monthcalendar(year, month)
        
        # Обновляем кнопки дней
        today = datetime.now().date()
        selected = self.selected_date.date()
        
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                btn = self.day_buttons[row_idx][col_idx]
                
                if day == 0:
                    # Пустая ячейка
                    btn.config(text="", state=tk.DISABLED, bg='grey')
                else:
                    btn.config(text=str(day), state=tk.NORMAL)
                    
                    # Подсветка сегодняшнего дня
                    current_date = datetime(year, month, day).date()
                    if current_date == today:
                        btn.config(bg='lightblue')
                    elif current_date == selected:
                        btn.config(bg='lightgreen')
                    else:
                        btn.config(bg='grey')
        
        # Очищаем оставшиеся кнопки (если месяц короче 6 недель)
        for row_idx in range(len(cal), 6):
            for col_idx in range(7):
                btn = self.day_buttons[row_idx][col_idx]
                btn.config(text="", state=tk.DISABLED, bg='grey')
    
    def _prev_month(self):
        """Перейти к предыдущему месяцу"""
        year = self.selected_date.year
        month = self.selected_date.month - 1
        
        if month == 0:
            month = 12
            year -= 1
        
        # Сохраняем день если возможно
        day = min(self.selected_date.day, calendar.monthrange(year, month)[1])
        self.selected_date = datetime(year, month, day)
        self._update_calendar()
    
    def _next_month(self):
        """Перейти к следующему месяцу"""
        year = self.selected_date.year
        month = self.selected_date.month + 1
        
        if month == 13:
            month = 1
            year += 1
        
        # Сохраняем день если возможно
        day = min(self.selected_date.day, calendar.monthrange(year, month)[1])
        self.selected_date = datetime(year, month, day)
        self._update_calendar()
    
    def _select_day(self, row, col):
        """Выбрать день"""
        btn = self.day_buttons[row][col]
        day_text = btn.cget("text")
       
        if day_text and btn.cget("state") == "active":
            day = int(day_text)
           
            self.selected_date = datetime(
                self.selected_date.year,
                self.selected_date.month,
                day
            )
            self.result = self.selected_date.strftime("%d.%m.%Y")
            self.window.destroy()
    
    def _select_today(self):
        """Выбрать сегодняшнюю дату"""
        self.selected_date = datetime.now()
        self.result = self.selected_date.strftime("%d.%m.%Y")
        self.window.destroy()
    
    def _clear_date(self):
        """Очистить дату"""
        self.result = ""
        self.window.destroy()
    
    def _cancel(self):
        """Отменить выбор"""
        self.result = None
        self.window.destroy()
    
    def get_date(self):
        """
        Получить выбранную дату
        
        Returns:
            str: Дата в формате "ДД.ММ.ГГГГ" или None если отменено
        """
        self.window.wait_window()
        return self.result


def create_date_picker(parent, textvariable=None, initial_date=None):
    """
    Создать поле ввода даты с кнопкой календаря
    
    Args:
        parent: Родительский виджет
        textvariable: Переменная для хранения даты
        initial_date: Начальная дата
        
    Returns:
        tuple: (frame, entry, button)
    """
    frame = tk.Frame(parent)
    
    # Поле ввода
    entry = ttk.Entry(frame, textvariable=textvariable, width=15)
    entry.pack(side=tk.LEFT, padx=(0, 5))
    
    # Кнопка календаря
    def open_calendar():
        # Парсим текущую дату из поля
        current_date = initial_date
        try:
            date_str = entry.get().strip()
            if date_str:
                current_date = datetime.strptime(date_str, "%d.%m.%Y")
        except:
            pass
        
        # Открываем календарь
        dialog = CalendarDialog(parent.winfo_toplevel(), current_date)
        selected = dialog.get_date()
        
        # Устанавливаем выбранную дату
        if selected is not None:
            entry.delete(0, tk.END)
            if selected:  # Не пустая строка
                entry.insert(0, selected)
    
    btn = tk.Button(
        frame, text="\u23F0", width=3,
        command=open_calendar
    )
    btn.pack(side=tk.LEFT)
    
    return frame, entry, btn

