# -*- coding: utf-8 -*-
"""
Окно для добавления/редактирования мероприятий
"""

import tkinter as tk
from tkinter import ttk, messagebox
from constants import SPORTS, MONTHS, EVENT_TYPES, COACHES
from models import Event
from styles import apply_styles, COLORS, create_styled_button
from estimate_generator import EstimateGenerator


class AddEventWindow:
    """Класс окна для добавления/редактирования мероприятия"""
    
    def __init__(self, parent, db, year: int, callback=None, event: Event = None):
        """
        Инициализация окна
        
        Args:
            parent: Родительское окно
            db: Объект базы данных
            year: Выбранный год
            callback: Функция обратного вызова после сохранения
            event: Мероприятие для редактирования (None для создания нового)
        """
        self.parent = parent
        self.db = db
        self.year = year
        self.callback = callback
        self.event = event
        
        # Список тренеров
        self.trainers_widgets = []  # Список виджетов для тренеров
        
        # Создаем окно
        self.window = tk.Toplevel(parent)
        self.window.title("ДЮСК Ямбург - " + ("Редактировать мероприятие" if event else "Добавить мероприятие"))
        self.window.geometry("900x700")  # Уменьшили высоту - есть прокрутка
        self.window.resizable(True, True)
        
        # Применяем единые стили
        apply_styles(self.window)
        
        # Центрируем окно
        self.window.transient(parent)
        self.window.grab_set()
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._create_widgets()
        
        # Заполняем поля если редактируем
        if self.event:
            self._fill_fields()
    
    def _create_widgets(self):
        """Создать виджеты формы"""
        # Создаем контейнер с прокруткой для всего содержимого
        container = ttk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas и Scrollbar для прокрутки всего окна
        self.main_canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.main_canvas.yview)
        
        # Основной фрейм с отступами (внутри canvas)
        main_frame = ttk.Frame(self.main_canvas, padding="10")
        
        # Привязываем прокрутку
        main_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Прокрутка колесиком мыши (для Windows и Red OS)
        def _on_mousewheel(event):
            if self.main_canvas.winfo_exists():
                self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_mousewheel_linux(event):
            if self.main_canvas.winfo_exists():
                if event.num == 4:
                    self.main_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.main_canvas.yview_scroll(1, "units")
        
        # Привязываем к контейнеру
        # Windows
        container.bind("<MouseWheel>", _on_mousewheel)
        self.main_canvas.bind("<MouseWheel>", _on_mousewheel)
        main_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Linux (Red OS)
        container.bind("<Button-4>", _on_mousewheel_linux)
        container.bind("<Button-5>", _on_mousewheel_linux)
        self.main_canvas.bind("<Button-4>", _on_mousewheel_linux)
        self.main_canvas.bind("<Button-5>", _on_mousewheel_linux)
        main_frame.bind("<Button-4>", _on_mousewheel_linux)
        main_frame.bind("<Button-5>", _on_mousewheel_linux)
        
        row = 0
        
        # Год (только для отображения)
        ttk.Label(main_frame, text="Год:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=str(self.year), font=('Arial', 10, 'bold')).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1
        
        # Вид спорта
        ttk.Label(main_frame, text="Вид спорта:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sport_var = tk.StringVar()
        self.sport_combo = ttk.Combobox(
            main_frame, textvariable=self.sport_var, values=SPORTS, state='readonly', width=40
        )
        self.sport_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.sport_combo.current(0)
        row += 1
        
        # Тип мероприятия
        ttk.Label(main_frame, text="Тип:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            main_frame, textvariable=self.type_var, values=EVENT_TYPES, state='readonly', width=40
        )
        self.type_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.type_combo.current(0)
        row += 1
        
        # Месяц
        ttk.Label(main_frame, text="Месяц:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.month_var = tk.StringVar()
        self.month_combo = ttk.Combobox(
            main_frame, textvariable=self.month_var, values=MONTHS, state='readonly', width=40
        )
        self.month_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.month_combo.current(0)
        row += 1
        
        # Название мероприятия
        ttk.Label(main_frame, text="Название:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        self.name_text = tk.Text(main_frame, height=4, width=40, wrap=tk.WORD)
        self.name_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Место проведения
        ttk.Label(main_frame, text="Место проведения:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.location_entry = ttk.Entry(main_frame, width=42)
        self.location_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Заложенная сумма на детей
        ttk.Label(main_frame, text="Сумма на детей:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.children_budget_entry = ttk.Entry(main_frame, width=42)
        self.children_budget_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.children_budget_entry.insert(0, "0")
        row += 1
        
        # Раздел тренеров
        ttk.Label(main_frame, text="Тренеры:", font=('Segoe UI', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        row += 1
        
        # Контейнер для списка тренеров с прокруткой
        trainers_container = tk.Frame(main_frame, bg=COLORS['bg'], relief='solid', bd=1)
        trainers_container.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Canvas и Scrollbar для прокрутки (вертикальная и горизонтальная)
        canvas = tk.Canvas(trainers_container, bg=COLORS['white'], height=180)  # Есть прокрутка всего окна
        scrollbar_y = ttk.Scrollbar(trainers_container, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(trainers_container, orient="horizontal", command=canvas.xview)
        self.trainers_frame = tk.Frame(canvas, bg=COLORS['white'])
        
        self.trainers_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.trainers_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Размещение canvas и scrollbar'ов
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        # Настройка растягивания контейнера
        trainers_container.grid_rowconfigure(0, weight=1)
        trainers_container.grid_columnconfigure(0, weight=1)
        
        row += 1
        
        # Кнопки управления тренерами
        trainers_buttons = tk.Frame(main_frame, bg=COLORS['bg'])
        trainers_buttons.grid(row=row, column=0, columnspan=2, pady=5)
        
        create_styled_button(
            trainers_buttons, 
            "➕ Добавить тренера", 
            self._add_trainer_row,
            style='secondary'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            trainers_buttons,
            text="(необязательно - можно добавить позже при уточнении)",
            font=('Segoe UI', 8),
            foreground=COLORS['text_light'],
            background=COLORS['bg']
        ).pack(side=tk.LEFT, padx=10)
        
        row += 1
        
        # Примечания
        ttk.Label(main_frame, text="Примечания:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        self.notes_text = tk.Text(main_frame, height=4, width=40, wrap=tk.WORD)
        self.notes_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Кнопки - в едином стиле
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        create_styled_button(button_frame, "💾 Сохранить", self._save, style='primary').pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, "Отмена", self.window.destroy, style='normal').pack(side=tk.LEFT, padx=5)
        
        # Настройка растягивания
        main_frame.columnconfigure(1, weight=1)
        
        # НЕ добавляем тренера по умолчанию - они необязательны
        # Тренеров можно будет добавить позже при уточнении деталей
    
    def _add_trainer_row(self, name="", budget=0):
        """Добавить строку для тренера"""
        row_frame = tk.Frame(self.trainers_frame, bg=COLORS['white'], relief='groove', bd=1)
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Номер тренера
        trainer_num = len(self.trainers_widgets) + 1
        ttk.Label(
            row_frame,
            text=f"#{trainer_num}",
            font=('Segoe UI', 9, 'bold'),
            width=3
        ).pack(side=tk.LEFT, padx=5)
        
        # ФИО тренера - выбор из списка
        ttk.Label(row_frame, text="ФИО:", width=5).pack(side=tk.LEFT, padx=2)
        
        # Если имя есть в списке - используем, иначе первое из списка
        selected_name = name if name and name in COACHES else COACHES[0]
        name_var = tk.StringVar(value=selected_name)
        name_entry = ttk.Combobox(row_frame, textvariable=name_var, values=COACHES, width=22, state='readonly')
        name_entry.pack(side=tk.LEFT, padx=5)
        
        # Бюджет
        ttk.Label(row_frame, text="Бюджет (₽):", width=10).pack(side=tk.LEFT, padx=2)
        budget_entry = ttk.Entry(row_frame, width=10)
        budget_entry.pack(side=tk.LEFT, padx=5)
        budget_entry.insert(0, str(budget))
        
        # Кнопка удалить - явная и заметная
        delete_btn = tk.Button(
            row_frame,
            text="🗑️ Удалить",
            command=lambda: self._remove_trainer_row(row_frame),
            bg='#dc3545',
            fg='white',
            font=('Segoe UI', 9),
            relief='raised',
            cursor='hand2',
            padx=8,
            pady=2
        )
        delete_btn.pack(side=tk.LEFT, padx=8)
        
        # Сохраняем ссылки на виджеты
        self.trainers_widgets.append({
            'frame': row_frame,
            'name': name_entry,
            'budget': budget_entry
        })
    
    def _remove_trainer_row(self, row_frame):
        """Удалить строку тренера"""
        # Находим и удаляем из списка
        for i, widget_dict in enumerate(self.trainers_widgets):
            if widget_dict['frame'] == row_frame:
                self.trainers_widgets.pop(i)
                break
        
        # Удаляем виджет
        row_frame.destroy()
        
        # Перенумеровываем оставшихся тренеров
        for i, widget_dict in enumerate(self.trainers_widgets, 1):
            # Обновляем номер в метке
            for widget in widget_dict['frame'].winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget('width') == 3:
                    widget.config(text=f"#{i}")
                    break
    
    def _fill_fields(self):
        """Заполнить поля данными мероприятия"""
        if not self.event:
            return
        
        # Устанавливаем значения
        self.sport_var.set(self.event.sport)
        self.type_var.set(self.event.event_type)
        self.month_var.set(self.event.month)
        
        self.name_text.delete('1.0', tk.END)
        self.name_text.insert('1.0', self.event.name)
        
        self.location_entry.delete(0, tk.END)
        self.location_entry.insert(0, self.event.location)
        
        self.children_budget_entry.delete(0, tk.END)
        self.children_budget_entry.insert(0, str(self.event.children_budget))
        
        # Загружаем тренеров из JSON
        if self.event.trainers_list:
            for trainer in self.event.trainers_list:
                self._add_trainer_row(
                    name=trainer.get('name', 'Тренер'),
                    budget=trainer.get('budget', 0)
                )
        else:
            # Если нет JSON, загружаем из старых полей
            if self.event.trainers_count and self.event.trainers_count > 0:
                budget_per_trainer = self.event.trainers_budget / self.event.trainers_count if self.event.trainers_budget else 0
                for i in range(self.event.trainers_count):
                    self._add_trainer_row(
                        name=f"Тренер {i+1}",
                        budget=budget_per_trainer
                    )
        
        self.notes_text.delete('1.0', tk.END)
        self.notes_text.insert('1.0', self.event.notes)
    
    def _validate_fields(self) -> bool:
        """Валидация полей формы"""
        # Проверка названия
        name = self.name_text.get('1.0', tk.END).strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название мероприятия")
            return False
        
        # Проверка места проведения
        if not self.location_entry.get().strip():
            messagebox.showerror("Ошибка", "Введите место проведения")
            return False
        
        # Проверка суммы на детей
        try:
            float(self.children_budget_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная сумма на детей")
            return False
        
        # Проверка данных тренеров (только если они добавлены)
        if self.trainers_widgets:
            for i, trainer_widget in enumerate(self.trainers_widgets, 1):
                # Проверка ФИО
                name = trainer_widget['name'].get().strip()
                if not name:
                    messagebox.showerror("Ошибка", f"Укажите ФИО для тренера #{i} или удалите его")
                    return False
                
                # Проверка бюджета
                try:
                    budget = float(trainer_widget['budget'].get())
                    if budget < 0:
                        messagebox.showerror("Ошибка", f"Бюджет для тренера #{i} не может быть отрицательным")
                        return False
                except ValueError:
                    messagebox.showerror("Ошибка", f"Некорректный бюджет для тренера #{i}")
                    return False
        
        return True
    
    def _save(self):
        """Сохранить мероприятие"""
        if not self._validate_fields():
            return
        
        # Собираем данные
        sport = self.sport_var.get()
        event_type = self.type_var.get()
        month = self.month_var.get()
        name = self.name_text.get('1.0', tk.END).strip()
        location = self.location_entry.get().strip()
        children_budget = float(self.children_budget_entry.get())
        notes = self.notes_text.get('1.0', tk.END).strip()
        
        # Собираем данные о тренерах (может быть пустой список)
        trainers_list = []
        for trainer_widget in self.trainers_widgets:
            trainer_name = trainer_widget['name'].get().strip()
            trainer_budget = float(trainer_widget['budget'].get())
            trainers_list.append({
                'name': trainer_name,
                'budget': trainer_budget
            })
        
        # Если тренеров нет - передаем None вместо пустого списка
        if not trainers_list:
            trainers_list = None
        
        try:
            event_id = None
            
            if self.event and self.event.id:
                # Обновляем существующее мероприятие (есть ID)
                self.db.update_event(
                    self.event.id, self.year, sport, event_type, name, location,
                    month, children_budget, trainers_list=trainers_list, notes=notes
                )
                event_id = self.event.id
                #messagebox.showinfo("Успешно", "Мероприятие обновлено")
            else:
                # Создаем новое мероприятие (нет ID или event=None)
                event_id = self.db.add_event(
                    self.year, sport, event_type, name, location, month,
                    children_budget, trainers_list=trainers_list, notes=notes
                )
                #messagebox.showinfo("Успешно", "Мероприятие добавлено")
                
                # Автоматически создаём сметы для выездных мероприятий
                if event_type == "Выездное":
                    # Получаем созданное мероприятие
                    event_data = self.db.get_event_by_id(event_id)
                    if event_data:
                        created_event = Event.from_db_row(event_data)
                        EstimateGenerator.auto_generate_estimates(self.db, created_event)
            
            # Вызываем callback если он есть
            if self.callback:
                self.callback()
            
            # Закрываем окно
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить мероприятие: {str(e)}")

