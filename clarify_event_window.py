# -*- coding: utf-8 -*-
"""
Окно для уточнения деталей мероприятия
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from styles import apply_styles, COLORS, create_styled_button
from models import Event
from calendar_widget import create_date_picker


class ClarifyEventWindow:
    """Класс окна для уточнения деталей мероприятия"""
    
    def __init__(self, parent, db, event: Event, callback=None):
        """
        Инициализация окна
        
        Args:
            parent: Родительское окно
            db: Объект базы данных
            event: Мероприятие для уточнения
            callback: Функция обратного вызова после сохранения
        """
        self.parent = parent
        self.db = db
        self.event = event
        self.callback = callback
        
        # Создаем окно
        self.window = tk.Toplevel(parent)
        self.window.title(f"ДЮСК Ямбург - Уточнить: {event.name[:40]}...")
        self.window.transient(parent)
        self.window.grab_set()
        
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
                self.window.geometry("900x800")
        
        # Применяем единые стили
        apply_styles(self.window)
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_widgets()
        self._fill_fields()
    
    def _create_widgets(self):
        """Создать виджеты формы"""
        # Создаем контейнер с прокруткой для всего содержимого
        container = ttk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas и Scrollbar для прокрутки всего окна
        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # Основной фрейм с отступами (внутри canvas)
        main_frame = ttk.Frame(self.canvas, padding="10")
        
        # Привязываем прокрутку
        main_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=main_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Прокрутка колесиком мыши (для Windows и Red OS)
        def _on_mousewheel(event):
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_mousewheel_linux(event):
            if self.canvas.winfo_exists():
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
        
        # Привязываем к контейнеру, а не глобально
        # Windows
        container.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        main_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Linux (Red OS)
        container.bind("<Button-4>", _on_mousewheel_linux)
        container.bind("<Button-5>", _on_mousewheel_linux)
        self.canvas.bind("<Button-4>", _on_mousewheel_linux)
        self.canvas.bind("<Button-5>", _on_mousewheel_linux)
        main_frame.bind("<Button-4>", _on_mousewheel_linux)
        main_frame.bind("<Button-5>", _on_mousewheel_linux)
        
        row = 0
        
        # Информация о мероприятии
        info_frame = ttk.LabelFrame(main_frame, text="Информация о мероприятии", padding="10")
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(info_frame, text=f"Название: {self.event.name}", wraplength=500).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Спорт: {self.event.sport}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Месяц: {self.event.month} {self.event.year}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Место: {self.event.location}").pack(anchor=tk.W, pady=2)
        
        # Информация о тренерах
        if self.event.trainers_list:
            ttk.Label(info_frame, text="Тренеры:", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
            for i, trainer in enumerate(self.event.trainers_list, 1):
                trainer_text = f"  {i}. {trainer.get('name', 'Без имени')} - {trainer.get('budget', 0):.2f} руб."
                ttk.Label(info_frame, text=trainer_text).pack(anchor=tk.W, pady=1, padx=10)
        else:
            ttk.Label(info_frame, text=f"Тренеров: {self.event.trainers_count} чел. на {self.event.trainers_budget:.2f} руб.").pack(anchor=tk.W, pady=2)
        
        row += 1
        
        # Статус мероприятия
        ttk.Label(main_frame, text="Статус:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=10
        )
        row += 1
        
        self.status_var = tk.StringVar(value=self.event.status or "Запланировано")
        
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(
            status_frame, text="Запланировано", variable=self.status_var, 
            value="Запланировано", command=self._on_status_change
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            status_frame, text="Проведено", variable=self.status_var, 
            value="Проведено", command=self._on_status_change
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            status_frame, text="Отменено", variable=self.status_var, 
            value="Отменено", command=self._on_status_change
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            status_frame, text="Перенесено", variable=self.status_var, 
            value="Перенесено", command=self._on_status_change
        ).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Фрейм для фактических данных (только для статуса "Проведено")
        self.actual_frame = ttk.LabelFrame(main_frame, text="Фактические данные", padding="10")
        self.actual_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        actual_row = 0
        
        # Фактические даты (с календарём)
        ttk.Label(self.actual_frame, text="Дата начала:").grid(
            row=actual_row, column=0, sticky=tk.W, pady=5
        )
        start_date_frame, self.start_date_entry, _ = create_date_picker(self.actual_frame)
        start_date_frame.grid(row=actual_row, column=1, sticky=tk.W, pady=5)
        ttk.Label(self.actual_frame, text="(ДД.ММ.ГГГГ или \u23F0)").grid(
            row=actual_row, column=2, sticky=tk.W, pady=5, padx=5
        )
        actual_row += 1
        
        ttk.Label(self.actual_frame, text="Дата окончания:").grid(
            row=actual_row, column=0, sticky=tk.W, pady=5
        )
        end_date_frame, self.end_date_entry, _ = create_date_picker(self.actual_frame)
        end_date_frame.grid(row=actual_row, column=1, sticky=tk.W, pady=5)
        ttk.Label(self.actual_frame, text="(ДД.ММ.ГГГГ или \u23F0)").grid(
            row=actual_row, column=2, sticky=tk.W, pady=5, padx=5
        )
        actual_row += 1
        
        # Фактически потраченные суммы
        ttk.Label(self.actual_frame, text="Фактическая сумма на детей:").grid(
            row=actual_row, column=0, sticky=tk.W, pady=5
        )
        self.actual_children_budget_entry = ttk.Entry(self.actual_frame, width=22)
        self.actual_children_budget_entry.grid(row=actual_row, column=1, sticky=tk.W, pady=5)
        ttk.Label(self.actual_frame, text=f"(план: {self.event.children_budget:.2f})").grid(
            row=actual_row, column=2, sticky=tk.W, pady=5, padx=5
        )
        actual_row += 1
        
        # Фактические расходы на тренеров (детально)
        if self.event.trainers_list:
            ttk.Label(self.actual_frame, text="Фактические расходы на тренеров:", font=('Segoe UI', 9, 'bold')).grid(
                row=actual_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5)
            )
            actual_row += 1
            
            # Создаем контейнер с прокруткой для списка тренеров
            trainers_scroll_container = tk.Frame(self.actual_frame, relief='solid', bd=1)
            trainers_scroll_container.grid(row=actual_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
            
            # Canvas для прокрутки
            trainers_canvas = tk.Canvas(trainers_scroll_container, height=180)  # Увеличили высоту для РЕД ОС
            scrollbar_x = ttk.Scrollbar(trainers_scroll_container, orient="horizontal", command=trainers_canvas.xview)
            scrollbar_y = ttk.Scrollbar(trainers_scroll_container, orient="vertical", command=trainers_canvas.yview)
            
            trainers_inner_frame = tk.Frame(trainers_canvas)
            trainers_inner_frame.bind(
                "<Configure>",
                lambda e: trainers_canvas.configure(scrollregion=trainers_canvas.bbox("all"))
            )
            
            trainers_canvas.create_window((0, 0), window=trainers_inner_frame, anchor="nw")
            trainers_canvas.configure(xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
            
            # Размещение
            trainers_canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar_y.grid(row=0, column=1, sticky="ns")
            scrollbar_x.grid(row=1, column=0, sticky="ew")
            
            trainers_scroll_container.grid_rowconfigure(0, weight=1)
            trainers_scroll_container.grid_columnconfigure(0, weight=1)
            
            # Добавляем тренеров в scrollable frame
            self.actual_trainers_widgets = []
            for i, trainer in enumerate(self.event.trainers_list):
                trainer_row = tk.Frame(trainers_inner_frame)
                trainer_row.pack(fill=tk.X, padx=5, pady=2)
                
                # ФИО тренера
                ttk.Label(trainer_row, text=f"{i+1}. {trainer.get('name', 'Тренер')}:", width=25).pack(side=tk.LEFT, padx=5)
                
                # Поле для фактической суммы
                ttk.Label(trainer_row, text="Факт:").pack(side=tk.LEFT, padx=2)
                actual_entry = ttk.Entry(trainer_row, width=12)
                actual_entry.pack(side=tk.LEFT, padx=5)
                
                # План
                plan_budget = trainer.get('budget', 0)
                ttk.Label(trainer_row, text=f"(план: {plan_budget:.2f})").pack(side=tk.LEFT, padx=5)
                
                self.actual_trainers_widgets.append({
                    'name': trainer.get('name', 'Тренер'),
                    'plan_budget': plan_budget,
                    'entry': actual_entry
                })
            
            actual_row += 1
        else:
            # Проверяем, есть ли тренеры вообще
            if self.event.trainers_count and self.event.trainers_count > 0:
                # Старый формат - общая сумма
                ttk.Label(self.actual_frame, text="Фактическая сумма на тренеров:").grid(
                    row=actual_row, column=0, sticky=tk.W, pady=5
                )
                self.actual_trainers_budget_entry = ttk.Entry(self.actual_frame, width=22)
                self.actual_trainers_budget_entry.grid(row=actual_row, column=1, sticky=tk.W, pady=5)
                ttk.Label(self.actual_frame, text=f"(план: {self.event.trainers_budget:.2f})").grid(
                    row=actual_row, column=2, sticky=tk.W, pady=5, padx=5
                )
                actual_row += 1
            else:
                # Тренеры не указаны
                from styles import FONT_FAMILY
                ttk.Label(
                    self.actual_frame, 
                    text="Тренеры не указаны. Добавьте их через кнопку 'Редактировать'.",
                    font=(FONT_FAMILY, 9, 'italic'),
                    foreground='gray'
                ).grid(row=actual_row, column=0, columnspan=3, sticky=tk.W, pady=5)
                actual_row += 1
            
            self.actual_trainers_widgets = []
        
        row += 1
        
        # Фрейм для причины отмены
        self.cancellation_frame = ttk.LabelFrame(
            main_frame, text="Причина отмены", padding="10"
        )
        self.cancellation_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.cancellation_text = tk.Text(
            self.cancellation_frame, height=4, width=60, wrap=tk.WORD
        )
        self.cancellation_text.pack(fill=tk.BOTH, expand=True)
        
        row += 1
        
        # Фрейм для причины переноса
        self.postponement_frame = ttk.LabelFrame(
            main_frame, text="Причина переноса", padding="10"
        )
        self.postponement_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.postponement_text = tk.Text(
            self.postponement_frame, height=4, width=60, wrap=tk.WORD
        )
        self.postponement_text.pack(fill=tk.BOTH, expand=True)
        
        row += 1
        
        # Кнопки - в едином стиле
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        create_styled_button(button_frame, "✏️ Сохранить изменения", self._save, style='accent').pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, "Отмена", self.window.destroy, style='normal').pack(side=tk.LEFT, padx=5)
        
        # Настройка растягивания
        main_frame.columnconfigure(1, weight=1)
    
    def _fill_fields(self):
        """Заполнить поля данными мероприятия"""
        # Статус уже установлен в создании виджетов
        
        # Фактические даты
        if self.event.actual_start_date:
            self.start_date_entry.insert(0, self.event.actual_start_date)
        
        if self.event.actual_end_date:
            self.end_date_entry.insert(0, self.event.actual_end_date)
        
        # Фактические суммы
        if self.event.actual_children_budget is not None:
            self.actual_children_budget_entry.insert(0, str(self.event.actual_children_budget))
        
        # Загрузка фактических данных тренеров
        if self.actual_trainers_widgets and self.event.actual_trainers_list:
            for i, widget_data in enumerate(self.actual_trainers_widgets):
                if i < len(self.event.actual_trainers_list):
                    actual_trainer = self.event.actual_trainers_list[i]
                    widget_data['entry'].insert(0, str(actual_trainer.get('actual_budget', '')))
        elif hasattr(self, 'actual_trainers_budget_entry') and self.event.actual_trainers_budget is not None:
            # Старый формат - общая сумма
            self.actual_trainers_budget_entry.insert(0, str(self.event.actual_trainers_budget))
        
        # Причины
        if self.event.cancellation_reason:
            self.cancellation_text.insert('1.0', self.event.cancellation_reason)
        
        if self.event.postponement_reason:
            self.postponement_text.insert('1.0', self.event.postponement_reason)
        
        # Показываем/скрываем нужные фреймы
        self._on_status_change()
    
    def _on_status_change(self):
        """Обработчик изменения статуса"""
        status = self.status_var.get()
        
        # Показываем/скрываем фреймы в зависимости от статуса
        if status == "Проведено":
            self.actual_frame.grid()
            self.cancellation_frame.grid_remove()
            self.postponement_frame.grid_remove()
        elif status == "Отменено":
            self.actual_frame.grid_remove()
            self.cancellation_frame.grid()
            self.postponement_frame.grid_remove()
        elif status == "Перенесено":
            self.actual_frame.grid_remove()
            self.cancellation_frame.grid_remove()
            self.postponement_frame.grid()
        else:  # Запланировано
            self.actual_frame.grid_remove()
            self.cancellation_frame.grid_remove()
            self.postponement_frame.grid_remove()
    
    def _on_close(self):
        """Обработчик закрытия окна"""
        self.window.destroy()
    
    def _validate_fields(self) -> bool:
        """Валидация полей формы"""
        status = self.status_var.get()
        
        if status == "Проведено":
            # Проверяем даты
            if self.start_date_entry.get().strip():
                try:
                    datetime.strptime(self.start_date_entry.get().strip(), '%d.%m.%Y')
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректная дата начала. Используйте формат ДД.ММ.ГГГГ")
                    return False
            
            if self.end_date_entry.get().strip():
                try:
                    datetime.strptime(self.end_date_entry.get().strip(), '%d.%m.%Y')
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректная дата окончания. Используйте формат ДД.ММ.ГГГГ")
                    return False
            
            # Проверяем фактические суммы
            try:
                if self.actual_children_budget_entry.get().strip():
                    float(self.actual_children_budget_entry.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректная фактическая сумма на детей")
                return False
            
            # Проверяем фактические суммы на тренеров
            if self.actual_trainers_widgets:
                # Детальная проверка для каждого тренера
                for widget_data in self.actual_trainers_widgets:
                    actual_str = widget_data['entry'].get().strip()
                    if actual_str:
                        try:
                            float(actual_str)
                        except ValueError:
                            messagebox.showerror("Ошибка", f"Некорректная сумма для тренера {widget_data['name']}")
                            return False
            elif hasattr(self, 'actual_trainers_budget_entry'):
                # Старый формат - общая сумма
                try:
                    if self.actual_trainers_budget_entry.get().strip():
                        float(self.actual_trainers_budget_entry.get())
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректная фактическая сумма на тренеров")
                    return False
        
        elif status == "Отменено":
            if not self.cancellation_text.get('1.0', tk.END).strip():
                messagebox.showerror("Ошибка", "Укажите причину отмены")
                return False
        
        elif status == "Перенесено":
            if not self.postponement_text.get('1.0', tk.END).strip():
                messagebox.showerror("Ошибка", "Укажите причину переноса")
                return False
        
        return True
    
    def _save(self):
        """Сохранить уточнения"""
        if not self._validate_fields():
            return
        
        status = self.status_var.get()
        
        # Собираем данные
        actual_start_date = None
        actual_end_date = None
        actual_children_budget = None
        actual_trainers_budget = None
        cancellation_reason = None
        postponement_reason = None
        
        if status == "Проведено":
            if self.start_date_entry.get().strip():
                actual_start_date = self.start_date_entry.get().strip()
            
            if self.end_date_entry.get().strip():
                actual_end_date = self.end_date_entry.get().strip()
            
            if self.actual_children_budget_entry.get().strip():
                actual_children_budget = float(self.actual_children_budget_entry.get())
            
            # Собираем фактические данные тренеров
            actual_trainers_list = []
            if self.actual_trainers_widgets:
                total_actual = 0
                for widget_data in self.actual_trainers_widgets:
                    actual_budget_str = widget_data['entry'].get().strip()
                    if actual_budget_str:
                        actual_budget = float(actual_budget_str)
                        total_actual += actual_budget
                        actual_trainers_list.append({
                            'name': widget_data['name'],
                            'plan_budget': widget_data['plan_budget'],
                            'actual_budget': actual_budget
                        })
                
                # Общая сумма на тренеров
                if actual_trainers_list:
                    actual_trainers_budget = total_actual
            elif hasattr(self, 'actual_trainers_budget_entry') and self.actual_trainers_budget_entry.get().strip():
                # Старый формат
                actual_trainers_budget = float(self.actual_trainers_budget_entry.get())
        
        elif status == "Отменено":
            cancellation_reason = self.cancellation_text.get('1.0', tk.END).strip()
        
        elif status == "Перенесено":
            postponement_reason = self.postponement_text.get('1.0', tk.END).strip()
        
        try:
            self.db.update_event_clarification(
                self.event.id, status, actual_start_date, actual_end_date,
                actual_children_budget, actual_trainers_budget,
                cancellation_reason, postponement_reason,
                actual_trainers_list=actual_trainers_list if 'actual_trainers_list' in locals() else None
            )
            messagebox.showinfo("Успешно", "Уточнения сохранены")
            
            # Вызываем callback если он есть
            if self.callback:
                self.callback()
            
            # Закрываем окно
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить уточнения: {str(e)}")

