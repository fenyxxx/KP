# -*- coding: utf-8 -*-
"""
Окно для импорта мероприятий из CSV файла
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from constants import SPORTS, MONTHS, EVENT_TYPES
from models import Event


class ImportCSVWindow:
    """Класс окна для импорта мероприятий из CSV"""
    
    def __init__(self, parent, db, year: int, callback=None):
        """
        Инициализация окна
        
        Args:
            parent: Родительское окно
            db: Объект базы данных
            year: Год для импорта
            callback: Функция обратного вызова после импорта
        """
        self.parent = parent
        self.db = db
        self.year = year
        self.callback = callback
        
        self.csv_data = []  # Данные из CSV
        self.csv_headers = []  # Заголовки из CSV
        self.column_mapping = {}  # Сопоставление колонок
        self.selected_sport = None  # Выбранный вид спорта для всего файла
        
        # Создаем окно
        self.window = tk.Toplevel(parent)
        self.window.title("Импорт из CSV")
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
                self.window.geometry("900x750")
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создать виджеты окна"""
        # Основной фрейм
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Панель выбора вида спорта
        sport_frame = ttk.LabelFrame(main_frame, text="Шаг 1: Выберите вид спорта для всего файла", padding="10")
        sport_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sport_frame, text="Вид спорта:").pack(side=tk.LEFT, padx=5)
        
        self.sport_var = tk.StringVar()
        self.sport_combo = ttk.Combobox(
            sport_frame, textvariable=self.sport_var, 
            values=SPORTS, state='readonly', width=30
        )
        self.sport_combo.pack(side=tk.LEFT, padx=5)
        self.sport_combo.current(0)
        
        ttk.Label(
            sport_frame, 
            text="(Все мероприятия в файле будут с этим видом спорта)",
            foreground="gray"
        ).pack(side=tk.LEFT, padx=10)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Верхняя панель с выбором файла
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="Шаг 2: Выберите CSV файл").pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Выбрать файл...", command=self._select_file).pack(side=tk.LEFT, padx=5)
        
        self.file_label = ttk.Label(top_frame, text="Файл не выбран", foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Панель сопоставления колонок
        self.mapping_frame = ttk.LabelFrame(main_frame, text="Шаг 3: Сопоставьте колонки CSV с полями программы", padding="10")
        self.mapping_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Создаем сопоставления
        self.mapping_combos = {}
        
        # Описание полей программы (вид спорта теперь необязательный, т.к. выбирается выше)
        program_fields = [
            ("Вид спорта (переопределит выбранный)", "sport", False),
            ("Тип (Внутреннее/Выездное)*", "event_type", True),
            ("Месяц*", "month", True),
            ("Название*", "name", True),
            ("Место проведения*", "location", True),
            ("Сумма на детей", "children_budget", False),
            ("Количество тренеров", "trainers_count", False),
            ("Сумма на тренеров", "trainers_budget", False),
            ("Примечания", "notes", False),
        ]
        
        ttk.Label(self.mapping_frame, text="Поле программы", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        ttk.Label(self.mapping_frame, text="Колонка в CSV", font=('Arial', 9, 'bold')).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        for i, (field_name, field_key, required) in enumerate(program_fields, 1):
            ttk.Label(self.mapping_frame, text=field_name).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            
            combo = ttk.Combobox(self.mapping_frame, width=30, state='readonly')
            combo.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
            self.mapping_combos[field_key] = combo
        
        ttk.Label(self.mapping_frame, text="* - обязательные поля", foreground="gray").grid(
            row=len(program_fields)+1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.mapping_frame.columnconfigure(1, weight=1)
        
        # Изначально скрываем
        self.mapping_frame.pack_forget()
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Предпросмотр данных
        self.preview_frame = ttk.LabelFrame(main_frame, text="Шаг 4: Предпросмотр данных", padding="10")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Таблица предпросмотра
        preview_table_frame = ttk.Frame(self.preview_frame)
        preview_table_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_tree = ttk.Treeview(preview_table_frame, show='headings', height=10)
        
        scrollbar_y = ttk.Scrollbar(preview_table_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        scrollbar_x = ttk.Scrollbar(preview_table_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.preview_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        preview_table_frame.grid_rowconfigure(0, weight=1)
        preview_table_frame.grid_columnconfigure(0, weight=1)
        
        self.preview_status = ttk.Label(self.preview_frame, text="Готово к импорту: 0 записей", foreground="gray")
        self.preview_status.pack(pady=5)
        
        # Изначально скрываем
        self.preview_frame.pack_forget()
        
        # Нижняя панель с кнопками
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.preview_button = ttk.Button(
            bottom_frame, text="Предпросмотр", command=self._preview_data, state='disabled'
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        self.import_button = ttk.Button(
            bottom_frame, text="Импортировать", command=self._import_data, state='disabled'
        )
        self.import_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(bottom_frame, text="Закрыть", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _select_file(self):
        """Выбрать CSV файл"""
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[
                ("CSV файлы", "*.csv"),
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Пробуем разные кодировки и разделители
            self.csv_data, self.csv_headers = self._read_csv_file(file_path)
            
            if not self.csv_data:
                messagebox.showerror("Ошибка", "CSV файл пуст или не удалось прочитать данные")
                return
            
            # Обновляем интерфейс
            self.file_label.config(text=file_path.split('/')[-1], foreground="black")
            
            # Заполняем комбобоксы колонок
            column_options = ["<Не использовать>"] + self.csv_headers
            for combo in self.mapping_combos.values():
                combo['values'] = column_options
                combo.current(0)
            
            # Пытаемся автоматически сопоставить колонки
            self._auto_map_columns()
            
            # Показываем панель сопоставления
            self.mapping_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Активируем кнопку предпросмотра
            self.preview_button.config(state='normal')
            
            messagebox.showinfo(
                "Успешно", 
                f"Загружено {len(self.csv_data)} строк с {len(self.csv_headers)} колонками"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
    
    def _read_csv_file(self, file_path):
        """Прочитать CSV файл с автоопределением кодировки и разделителя"""
        encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'windows-1251', 'latin-1']
        delimiters = [';', ',', '\t', '|']
        
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Читаем первую строку для проверки
                        sample = f.read(1024)
                        f.seek(0)
                        
                        # Проверяем, подходит ли разделитель
                        if delimiter not in sample:
                            continue
                        
                        reader = csv.DictReader(f, delimiter=delimiter)
                        headers = reader.fieldnames
                        
                        if not headers:
                            continue
                        
                        data = list(reader)
                        
                        if data:
                            return data, headers
                            
                except Exception:
                    continue
        
        raise Exception("Не удалось определить формат файла. Попробуйте другой файл.")
    
    def _auto_map_columns(self):
        """Автоматическое сопоставление колонок по похожим названиям"""
        # Словарь похожих названий
        similar_names = {
            'sport': ['вид спорта', 'спорт', 'вид', 'sport'],
            'event_type': ['тип', 'type', 'внутреннее', 'выездное'],
            'month': ['месяц', 'month', 'период'],
            'name': ['название', 'наименование', 'мероприятие', 'name', 'event'],
            'location': ['место', 'город', 'location', 'place', 'venue'],
            'children_budget': ['сумма на детей', 'дети', 'бюджет детей', 'children'],
            'trainers_count': ['количество тренеров', 'тренеров', 'тренеры', 'trainers'],
            'trainers_budget': ['сумма на тренеров', 'бюджет тренеров', 'trainers budget'],
            'notes': ['примечания', 'комментарий', 'notes', 'comment'],
        }
        
        for field_key, combo in self.mapping_combos.items():
            # Пробуем найти похожую колонку
            for csv_header in self.csv_headers:
                header_lower = csv_header.lower().strip()
                
                if field_key in similar_names:
                    for similar in similar_names[field_key]:
                        if similar in header_lower:
                            # Находим индекс в списке values
                            try:
                                index = combo['values'].index(csv_header)
                                combo.current(index)
                                break
                            except ValueError:
                                pass
    
    def _preview_data(self):
        """Предпросмотр данных перед импортом"""
        # Сохраняем выбранный вид спорта
        self.selected_sport = self.sport_var.get()
        
        # Получаем сопоставление колонок
        self.column_mapping = {}
        for field_key, combo in self.mapping_combos.items():
            selected = combo.get()
            if selected and selected != "<Не использовать>":
                self.column_mapping[field_key] = selected
        
        # Проверяем обязательные поля (sport теперь необязательный, берется из выбора)
        required_fields = ['event_type', 'month', 'name', 'location']
        missing_fields = []
        
        for field in required_fields:
            if field not in self.column_mapping:
                missing_fields.append(field)
        
        if missing_fields:
            messagebox.showerror(
                "Ошибка", 
                "Не сопоставлены обязательные поля:\n" + "\n".join(missing_fields)
            )
            return
        
        # Очищаем таблицу предпросмотра
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Настраиваем колонки
        columns = ['#', 'Статус'] + list(self.column_mapping.keys())
        self.preview_tree['columns'] = columns
        
        self.preview_tree.heading('#', text='#')
        self.preview_tree.heading('Статус', text='Статус')
        self.preview_tree.column('#', width=40)
        self.preview_tree.column('Статус', width=80)
        
        for col in self.column_mapping.keys():
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=100)
        
        # Заполняем данные с валидацией
        valid_count = 0
        
        for i, row in enumerate(self.csv_data[:100], 1):  # Показываем первые 100
            values = {'#': i}
            status = "✓ OK"
            
            # Собираем данные из строки
            for field_key, csv_column in self.column_mapping.items():
                value = row.get(csv_column, '').strip()
                values[field_key] = value
            
            # Если вид спорта не в CSV, используем выбранный
            if 'sport' not in values or not values.get('sport'):
                values['sport'] = self.selected_sport
            
            # Валидация
            errors = self._validate_row(values)
            if errors:
                status = "✗ Ошибка"
            else:
                valid_count += 1
            
            values['Статус'] = status
            
            # Добавляем в таблицу
            row_values = [values.get(col, '') for col in columns]
            self.preview_tree.insert('', tk.END, values=row_values)
        
        # Показываем фрейм предпросмотра
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Обновляем статус
        total = len(self.csv_data)
        self.preview_status.config(
            text=f"Готово к импорту: {valid_count} из {total} записей"
        )
        
        # Активируем кнопку импорта
        if valid_count > 0:
            self.import_button.config(state='normal')
        
        messagebox.showinfo(
            "Предпросмотр", 
            f"Валидных записей: {valid_count} из {total}\n" +
            (f"Показаны первые 100 записей" if total > 100 else "")
        )
    
    def _normalize_sport(self, sport_value):
        """Нормализация вида спорта - подбор из констант"""
        if not sport_value:
            return None
        
        sport_lower = sport_value.lower().strip()
        
        # Точное совпадение
        for sport in SPORTS:
            if sport.lower() == sport_lower:
                return sport
        
        # Частичное совпадение (содержит)
        for sport in SPORTS:
            if sport_lower in sport.lower() or sport.lower() in sport_lower:
                return sport
        
        # Словарь альтернативных названий
        sport_aliases = {
            'Бокс': ['бокс', 'boxing'],
            'Волейбол': ['волейбол', 'волейболл', 'volleyball', 'вб'],
            'Киокусинкай': ['киокусинкай', 'киокушинкай', 'каратэ', 'карате', 'kyokushin'],
            'Лыжные гонки': ['лыжи', 'лыжные', 'лыжн', 'ski', 'skiing'],
            'Настольный тенис': ['настольный теннис', 'настольный тенис', 'тенис', 'теннис', 'нт', 'table tennis', 'пинг-понг'],
            'Плавание': ['плавание', 'плаванье', 'бассейн', 'swimming'],
            'Танцевальный спорт': ['танцы', 'танцевальный', 'танец', 'dance', 'dancing'],
            'Футзал': ['футзал', 'футбол', 'мини-футбол', 'мини футбол', 'футсал', 'futsal', 'football']
        }
        
        for sport, aliases in sport_aliases.items():
            for alias in aliases:
                if alias in sport_lower or sport_lower in alias:
                    return sport
        
        return None
    
    def _normalize_event_type(self, type_value):
        """Нормализация типа мероприятия"""
        if not type_value:
            return None
        
        type_lower = type_value.lower().strip()
        
        # Проверяем ключевые слова
        if any(word in type_lower for word in ['внутр', 'внутренн']):
            return 'Внутреннее'
        if any(word in type_lower for word in ['выезд', 'выездн']):
            return 'Выездное'
        
        return None
    
    def _normalize_month(self, month_value):
        """Нормализация месяца"""
        if not month_value:
            return None
        
        month_lower = month_value.lower().strip()
        
        # Точное совпадение
        for month in MONTHS:
            if month.lower() == month_lower:
                return month
        
        # Частичное совпадение
        for month in MONTHS:
            if month_lower in month.lower() or month.lower() in month_lower:
                return month
        
        # Английские названия
        month_translations = {
            'january': 'Январь', 'jan': 'Январь',
            'february': 'Февраль', 'feb': 'Февраль',
            'march': 'Март', 'mar': 'Март',
            'april': 'Апрель', 'apr': 'Апрель',
            'may': 'Май',
            'june': 'Июнь', 'jun': 'Июнь',
            'july': 'Июль', 'jul': 'Июль',
            'august': 'Август', 'aug': 'Август',
            'september': 'Сентябрь', 'sep': 'Сентябрь', 'sept': 'Сентябрь',
            'october': 'Октябрь', 'oct': 'Октябрь',
            'november': 'Ноябрь', 'nov': 'Ноябрь',
            'december': 'Декабрь', 'dec': 'Декабрь'
        }
        
        if month_lower in month_translations:
            return month_translations[month_lower]
        
        return None
    
    def _validate_row(self, values):
        """Валидация одной строки данных"""
        errors = []
        
        # Проверка обязательных полей
        if not values.get('sport'):
            errors.append("Отсутствует вид спорта")
        if not values.get('event_type'):
            errors.append("Отсутствует тип мероприятия")
        if not values.get('month'):
            errors.append("Отсутствует месяц")
        if not values.get('name'):
            errors.append("Отсутствует название")
        if not values.get('location'):
            errors.append("Отсутствует место проведения")
        
        # Проверка вида спорта (с нормализацией)
        if values.get('sport'):
            normalized_sport = self._normalize_sport(values['sport'])
            if not normalized_sport:
                errors.append(f"Неизвестный вид спорта: {values['sport']}")
            else:
                values['sport'] = normalized_sport  # Заменяем на нормализованное значение
        
        # Проверка типа (с нормализацией)
        if values.get('event_type'):
            normalized_type = self._normalize_event_type(values['event_type'])
            if not normalized_type:
                errors.append(f"Неизвестный тип: {values['event_type']}")
            else:
                values['event_type'] = normalized_type
        
        # Проверка месяца (с нормализацией)
        if values.get('month'):
            normalized_month = self._normalize_month(values['month'])
            if not normalized_month:
                errors.append(f"Неизвестный месяц: {values['month']}")
            else:
                values['month'] = normalized_month
        
        # Проверка сумм (необязательные)
        if values.get('children_budget'):
            try:
                float(values['children_budget'])
            except ValueError:
                errors.append(f"Некорректная сумма на детей: {values['children_budget']}")
        
        if values.get('trainers_budget'):
            try:
                float(values['trainers_budget'])
            except ValueError:
                errors.append(f"Некорректная сумма на тренеров: {values['trainers_budget']}")
        
        # Проверка количества тренеров (необязательное)
        if values.get('trainers_count'):
            try:
                int(values['trainers_count'])
            except ValueError:
                errors.append(f"Некорректное количество тренеров: {values['trainers_count']}")
        
        return errors
    
    def _import_data(self):
        """Импортировать данные в базу"""
        if not messagebox.askyesno(
            "Подтверждение", 
            f"Импортировать мероприятия в {self.year} год?\n\n" +
            "Это добавит новые записи в базу данных."
        ):
            return
        
        imported_count = 0
        error_count = 0
        
        for row in self.csv_data:
            # Собираем данные
            values = {}
            for field_key, csv_column in self.column_mapping.items():
                values[field_key] = row.get(csv_column, '').strip()
            
            # Если вид спорта не в CSV, используем выбранный
            if 'sport' not in values or not values.get('sport'):
                values['sport'] = self.selected_sport
            
            # Валидация
            errors = self._validate_row(values)
            if errors:
                error_count += 1
                continue
            
            try:
                # Нормализация обязательных полей
                sport = self._normalize_sport(values.get('sport', '')) or ''
                event_type = self._normalize_event_type(values.get('event_type', '')) or ''
                month = self._normalize_month(values.get('month', '')) or ''
                name = values.get('name', '').strip()
                location = values.get('location', '').strip()
                
                # Необязательные поля с значениями по умолчанию
                children_budget = float(values.get('children_budget', 0)) if values.get('children_budget') else 0.0
                trainers_count = int(values.get('trainers_count', 1)) if values.get('trainers_count') else 1
                trainers_budget = float(values.get('trainers_budget', 0)) if values.get('trainers_budget') else 0.0
                notes = values.get('notes', '').strip()
                
                # Добавляем в БД
                self.db.add_event(
                    self.year, sport, event_type, name, location, month,
                    children_budget, trainers_count, trainers_budget, notes
                )
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Ошибка импорта строки: {e}")
        
        # Результат
        messagebox.showinfo(
            "Импорт завершен",
            f"Успешно импортировано: {imported_count}\n" +
            f"Ошибок: {error_count}"
        )
        
        # Вызываем callback если есть
        if self.callback:
            self.callback()
        
        # Закрываем окно
        self.window.destroy()

