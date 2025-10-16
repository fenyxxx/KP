# -*- coding: utf-8 -*-
"""
Главное окно приложения
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
from database import Database
from models import Event
from add_event_window import AddEventWindow
from view_plan_window import ViewPlanWindow
from clarify_event_window import ClarifyEventWindow
from import_csv_window import ImportCSVWindow
from backup_window import BackupWindow
from backup_manager import BackupManager
from data_check_window import DataCheckWindow
from estimate_window import EstimateWindow
from constants import SPORTS, MONTHS
from styles import FONT_FAMILY, MONOSPACE_FONT


def format_rubles(amount):
    """
    Форматировать сумму в российском стиле с разделителями
    
    Args:
        amount: Сумма в рублях
        
    Returns:
        Отформатированная строка (например: "1 234 567 руб.")
    """
    if amount == 0:
        return "0 руб."
    
    # Округляем до рублей
    amount = int(round(amount))
    
    # Форматируем с пробелами как разделителями тысяч
    formatted = "{:,}".format(amount).replace(',', ' ')
    
    return f"{formatted} руб."


def format_rubles_compact(amount):
    """
    Форматировать сумму компактно (без "руб.") для таблиц
    
    Args:
        amount: Сумма в рублях
        
    Returns:
        Отформатированная строка (например: "1 234 567")
    """
    if amount == 0:
        return "0"
    
    # Округляем до рублей
    amount = int(round(amount))
    
    # Форматируем с пробелами как разделителями тысяч
    formatted = "{:,}".format(amount).replace(',', ' ')
    
    return formatted


class MainWindow:
    """Класс главного окна приложения"""
    
    def __init__(self, root):
        """
        Инициализация главного окна
        
        Args:
            root: Корневой виджет tkinter
        """
        self.root = root
        self.root.title("ДЮСК Ямбург - Календарные планы")
        
        # Разворачиваем окно на весь экран (кроссплатформенно)
        try:
            # Пробуем Windows-способ
            self.root.state('zoomed')
        except:
            # Для Linux (Red OS) - разворачиваем через geometry
            try:
                # Получаем размер экрана
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            except:
                # Если и это не работает, устанавливаем большой размер
                self.root.geometry("1400x900")
        
        # Устанавливаем минимальный размер окна
        self.root.minsize(1200, 700)
        
        # Корпоративные цвета ПАО Газпром
        self.colors = {
            'primary': '#0066B3',      # Синий Газпром
            'primary_dark': '#004B87',  # Тёмно-синий
            'primary_light': '#3399CC', # Светло-синий
            'accent': '#FF6B00',        # Оранжевый акцент (корпоративный)
            'bg': '#F5F7FA',            # Светлый фон
            'bg_dark': '#E8EEF4',       # Тёмный фон
            'text': '#2C3E50',          # Тёмный текст
            'text_light': '#7F8C8D',    # Светлый текст
            'white': '#FFFFFF',
            'border': '#BDC3C7'
        }
        
        # Применяем современный стиль
        self._setup_styles()
        
        # Инициализация БД
        self.db = Database()
        
        # Инициализация менеджера резервных копий
        self.backup_manager = BackupManager()
        
        # Автоматическое резервное копирование при запуске (раз в день)
        self._auto_backup()
        
        # Текущий год
        self.current_year = datetime.now().year
        self.selected_year = tk.IntVar(value=self.current_year)
        
        # Переменная для поиска
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._load_events())
        
        # Переменные для сортировки
        self.sort_column = None
        self.sort_reverse = False
        
        self._create_menu()
        self._create_widgets()
        self._setup_hotkeys()
        self._load_events()
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """Настроить современные стили в корпоративных цветах"""
        style = ttk.Style()
        
        # Основной фон окна
        self.root.configure(bg=self.colors['bg'])
        
        # Стиль для Frame
        style.configure('TFrame', background=self.colors['bg'])
        
        # Стиль для Label
        style.configure('TLabel', 
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=(FONT_FAMILY, 10))
        
        # Стиль для заголовков
        style.configure('Header.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['primary'],
                       font=(FONT_FAMILY, 12, 'bold'))
        
        # Стиль для кнопок
        style.configure('TButton',
                       font=(FONT_FAMILY, 10),
                       padding=8)
        
        # Акцентная кнопка (синяя)
        style.configure('Accent.TButton',
                       font=(FONT_FAMILY, 11, 'bold'))
        
        # Стиль для Combobox
        style.configure('TCombobox',
                       font=(FONT_FAMILY, 10))
        
        # Стиль для Entry
        style.configure('TEntry',
                       font=(FONT_FAMILY, 10))
        
        # Стиль для Treeview (таблица)
        style.configure('Treeview',
                       background=self.colors['white'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['white'],
                       font=(FONT_FAMILY, 9),
                       rowheight=28)
        
        # ВАЖНО: Заголовки таблицы - увеличены для видимости
        # Используем theme_use для корректного применения стилей
        try:
            style.theme_use('clam')  # Тема которая лучше работает с цветами
        except:
            pass
        
        style.configure('Treeview.Heading',
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       font=(FONT_FAMILY, 11, 'bold'),
                       relief='raised',
                       borderwidth=2)
        
        # Hover эффект для заголовков
        style.map('Treeview.Heading',
                 background=[('active', self.colors['primary_dark']), ('!active', self.colors['primary'])],
                 foreground=[('active', self.colors['white']), ('!active', self.colors['white'])],
                 relief=[('active', 'sunken'), ('!active', 'raised')])
        
        # Стили для выбранных строк
        style.map('Treeview',
                 background=[('selected', self.colors['primary_light'])],
                 foreground=[('selected', self.colors['white'])])
    
    def _create_menu(self):
        """Создать меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        file_menu.add_command(
            label="Создать мероприятие", 
            command=self._add_event,
            accelerator="Ctrl+N"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Импорт из CSV...", 
            command=self._import_from_csv
        )
        file_menu.add_command(
            label="Экспорт в CSV...", 
            command=self._export_to_csv
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Резервное копирование...", 
            command=self._open_backup_window
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Выход", 
            command=self.root.quit,
            accelerator="Alt+F4"
        )
        
        # Меню "Редактирование"
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Редактирование", menu=edit_menu)
        
        edit_menu.add_command(
            label="Редактировать", 
            command=self._edit_event,
            accelerator="Ctrl+E"
        )
        edit_menu.add_command(
            label="Дублировать", 
            command=self._duplicate_event,
            accelerator="Ctrl+D"
        )
        edit_menu.add_command(
            label="Удалить", 
            command=self._delete_event,
            accelerator="Delete"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="✏️ Уточнить детали", 
            command=self._clarify_event
        )
        edit_menu.add_command(
            label="📋 Сметы (выездные)", 
            command=self._manage_estimates
        )
        
        # Меню "Отчёты"
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Отчёты", menu=reports_menu)
        
        reports_menu.add_command(
            label="📊 Все отчёты...", 
            command=self._view_plan
        )
        reports_menu.add_separator()
        
        # Быстрый доступ к отчётам
        reports_menu.add_command(
            label="📈 По видам спорта",
            command=lambda: self._open_report_direct('by_sport')
        )
        reports_menu.add_command(
            label="📅 По месяцам",
            command=lambda: self._open_report_direct('by_month')
        )
        reports_menu.add_command(
            label="🏆 По типам мероприятий",
            command=lambda: self._open_report_direct('by_event_type')
        )
        reports_menu.add_command(
            label="✅ По статусам",
            command=lambda: self._open_report_direct('by_status')
        )
        reports_menu.add_command(
            label="👥 По тренерам",
            command=lambda: self._open_report_direct('by_trainers')
        )
        reports_menu.add_command(
            label="💰 По типам мероприятий (Выездные/Внутренние)",
            command=lambda: self._open_report_direct('by_type')
        )
        reports_menu.add_separator()
        reports_menu.add_command(
            label="📊 Годовой отчет ППО",
            command=lambda: self._open_report_direct('annual_ppo')
        )
        reports_menu.add_command(
            label="📋 Годовой отчет УЭВП",
            command=lambda: self._open_report_direct('annual_uevp')
        )
        
        # Меню "Просмотр"
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Просмотр", menu=view_menu)
        
        view_menu.add_command(
            label="🔍 Проверить данные", 
            command=self._check_data
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Обновить", 
            command=self._load_events,
            accelerator="F5"
        )
        view_menu.add_command(
            label="Сбросить фильтры", 
            command=self._reset_filters
        )
        view_menu.add_separator()
        view_menu.add_checkbutton(
            label="Показать строку поиска",
            state="disabled"  # Всегда включено
        )
        
        # Меню "Фильтры"
        filter_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Фильтры", menu=filter_menu)
        
        # Подменю "По виду спорта"
        sport_submenu = tk.Menu(filter_menu, tearoff=0)
        filter_menu.add_cascade(label="По виду спорта", menu=sport_submenu)
        
        sport_submenu.add_command(
            label="Все виды спорта",
            command=lambda: self._apply_sport_filter("Все")
        )
        sport_submenu.add_separator()
        for sport in SPORTS:
            sport_submenu.add_command(
                label=sport,
                command=lambda s=sport: self._apply_sport_filter(s)
            )
        
        # Подменю "По месяцу"
        month_submenu = tk.Menu(filter_menu, tearoff=0)
        filter_menu.add_cascade(label="По месяцу", menu=month_submenu)
        
        month_submenu.add_command(
            label="Все месяцы",
            command=lambda: self._apply_month_filter("Все")
        )
        month_submenu.add_separator()
        for month in MONTHS:
            month_submenu.add_command(
                label=month,
                command=lambda m=month: self._apply_month_filter(m)
            )
        
        filter_menu.add_separator()
        filter_menu.add_command(
            label="Сбросить все фильтры",
            command=self._reset_filters
        )
        
        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        
        help_menu.add_command(
            label="Горячие клавиши", 
            command=self._show_hotkeys_help
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="О программе", 
            command=self._show_about
        )
    
    def _create_widgets(self):
        """Создать виджеты главного окна"""
        # Инициализация переменных фильтров (для меню)
        self.sport_filter_var = tk.StringVar(value="Все")
        self.month_filter_var = tk.StringVar(value="Все")
        
        # Верхняя панель - компактная с современным дизайном
        top_frame = ttk.Frame(self.root, padding="15")
        top_frame.pack(fill=tk.X)
        
        # Левая часть: Год
        left_section = ttk.Frame(top_frame)
        left_section.pack(side=tk.LEFT)
        
        ttk.Label(left_section, text="Год:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        
        # Стильный Spinbox для года
        year_frame = tk.Frame(left_section, bg=self.colors['white'], relief='solid', bd=1)
        year_frame.pack(side=tk.LEFT)
        
        self.year_spinbox = tk.Spinbox(
            year_frame,
            from_=2020,
            to=2050,
            textvariable=self.selected_year,
            width=8,
            font=(FONT_FAMILY, 12, 'bold'),
            command=self._on_year_change,
            bg=self.colors['white'],
            fg=self.colors['primary'],
            relief='flat',
            buttonbackground=self.colors['primary'],
            bd=0
        )
        self.year_spinbox.pack(padx=5, pady=3)
        
        # Разделитель
        separator = ttk.Frame(top_frame, width=2)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=20)
        
        # Правая часть: Поиск
        search_section = ttk.Frame(top_frame)
        search_section.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_section, text="Быстрый поиск:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        
        # Стильное поле поиска
        search_frame = tk.Frame(search_section, bg=self.colors['white'], relief='solid', bd=1)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        search_entry = tk.Entry(
            search_frame, 
            textvariable=self.search_var, 
            font=(FONT_FAMILY, 10),
            bg=self.colors['white'],
            fg=self.colors['text'],
            relief='flat',
            bd=0
        )
        search_entry.pack(fill=tk.X, padx=8, pady=6)
        
        tk.Label(
            search_section, 
            text="(название, место, примечания)", 
            font=(FONT_FAMILY, 8),
            foreground=self.colors['text_light']
        ).pack(side=tk.LEFT, padx=8)
        
        # Дашборд со статистикой
        self._create_dashboard()
        
        # Быстрые фильтры
        self._create_quick_filters()
        
        # Кнопки действий - современный дизайн
        button_frame = ttk.Frame(self.root, padding="15 10")
        button_frame.pack(fill=tk.X)
        
        # Основные операции - в стиле Газпром
        btn_add = tk.Button(
            button_frame, 
            text="➕ Добавить мероприятие", 
            command=self._add_event,
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=(FONT_FAMILY, 10, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=8,
            activebackground=self.colors['primary_dark'],
            activeforeground=self.colors['white']
        )
        btn_add.pack(side=tk.LEFT, padx=5)
        
        # Эффект hover для кнопок
        def make_hover(button, color_normal, color_hover):
            def on_enter(e):
                button['bg'] = color_hover
            def on_leave(e):
                button['bg'] = color_normal
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)
        
        make_hover(btn_add, self.colors['primary'], self.colors['primary_dark'])
        
        btn_edit = tk.Button(
            button_frame, 
            text="✏️ Редактировать",
            command=self._edit_event,
            bg=self.colors['primary_light'],
            fg=self.colors['white'],
            font=(FONT_FAMILY, 10),
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=8,
            activebackground=self.colors['primary'],
            activeforeground=self.colors['white']
        )
        btn_edit.pack(side=tk.LEFT, padx=5)
        make_hover(btn_edit, self.colors['primary_light'], self.colors['primary'])
        
        btn_delete = tk.Button(
            button_frame, 
            text="🗑️ Удалить",
            command=self._delete_event,
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            font=(FONT_FAMILY, 10),
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=8,
            activebackground=self.colors['border'],
            activeforeground=self.colors['text']
        )
        btn_delete.pack(side=tk.LEFT, padx=5)
        make_hover(btn_delete, self.colors['bg_dark'], self.colors['border'])
        
        btn_duplicate = tk.Button(
            button_frame, 
            text="📋 Дублировать",
            command=self._duplicate_event,
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            font=(FONT_FAMILY, 10),
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=8,
            activebackground=self.colors['border'],
            activeforeground=self.colors['text']
        )
        btn_duplicate.pack(side=tk.LEFT, padx=5)
        make_hover(btn_duplicate, self.colors['bg_dark'], self.colors['border'])
        
        # Визуальный разделитель
        separator_frame = tk.Frame(button_frame, width=2, bg=self.colors['border'])
        separator_frame.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=5)
        
        # Кнопка "Уточнить детали" - ГЛАВНАЯ, оранжевая (корпоративный акцент), выделенная
        clarify_btn = tk.Button(
            button_frame, 
            text="✏️ УТОЧНИТЬ ДЕТАЛИ", 
            command=self._clarify_event,
            bg=self.colors['accent'],
            fg=self.colors['white'],
            font=(FONT_FAMILY, 11, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10,
            activebackground='#E55D00',
            activeforeground=self.colors['white']
        )
        clarify_btn.pack(side=tk.LEFT, padx=15)
        make_hover(clarify_btn, self.colors['accent'], '#E55D00')
        
        # Кнопка "Сметы" для выездных мероприятий
        estimates_btn = tk.Button(
            button_frame,
            text="📋 СМЕТЫ",
            command=self._manage_estimates,
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=(FONT_FAMILY, 11, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10,
            activebackground=self.colors['primary_dark'],
            activeforeground=self.colors['white']
        )
        estimates_btn.pack(side=tk.LEFT, padx=5)
        make_hover(estimates_btn, self.colors['primary'], self.colors['primary_dark'])
        
        # Остальные функции доступны через меню
        
        # Таблица с мероприятиями
        table_frame = ttk.Frame(self.root, padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview с новой колонкой "★"
        columns = ('★', 'Статус', 'Месяц', 'Тип', 'Спорт', 'Название', 'Место', 'Сумма на детей', 'Тренеры', 'Изменено')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Применяем стиль к дереву
        tree_style = ttk.Style()
        tree_style.configure('Custom.Treeview', 
                           background=self.colors['white'],
                           foreground=self.colors['text'],
                           fieldbackground=self.colors['white'],
                           rowheight=28,
                           font=(FONT_FAMILY, 9))
        
        tree_style.configure('Custom.Treeview.Heading',
                           background='#87CEEB',  # Голубой (Sky Blue)
                           foreground=self.colors['text'],  # Тёмный текст для контраста
                           font=(FONT_FAMILY, 11, 'bold'),
                           borderwidth=2,
                           relief='raised',
                           padding=8)
        
        # Явно указываем цвета для всех состояний
        tree_style.map('Custom.Treeview.Heading',
                      background=[
                          ('pressed', '#5DADE2'),  # Более яркий голубой при клике
                          ('active', '#5DADE2'),   # Более яркий голубой при наведении
                          ('!active', '#87CEEB'),  # Обычный голубой
                          ('disabled', '#87CEEB')
                      ],
                      foreground=[
                          ('pressed', self.colors['text']),
                          ('active', self.colors['text']),
                          ('!active', self.colors['text']),
                          ('disabled', self.colors['text'])
                      ])
        
        # Применяем кастомный стиль
        self.tree.configure(style='Custom.Treeview')
        
        # Настраиваем столбцы с сортировкой
        self.tree.heading('★', text='★', command=lambda: self._sort_by_column('★'))
        self.tree.heading('Статус', text='Статус ▲▼', command=lambda: self._sort_by_column('Статус'))
        self.tree.heading('Месяц', text='Месяц ▲▼', command=lambda: self._sort_by_column('Месяц'))
        self.tree.heading('Тип', text='Тип ▲▼', command=lambda: self._sort_by_column('Тип'))
        self.tree.heading('Спорт', text='Спорт ▲▼', command=lambda: self._sort_by_column('Спорт'))
        self.tree.heading('Название', text='Название ▲▼', command=lambda: self._sort_by_column('Название'))
        self.tree.heading('Место', text='Место ▲▼', command=lambda: self._sort_by_column('Место'))
        self.tree.heading('Сумма на детей', text='Сумма на детей (₽) ▲▼', command=lambda: self._sort_by_column('Сумма на детей'))
        self.tree.heading('Тренеры', text='Тренеры ▲▼', command=lambda: self._sort_by_column('Тренеры'))
        self.tree.heading('Изменено', text='Изменено ▲▼', command=lambda: self._sort_by_column('Изменено'))
        
        self.tree.column('★', width=50, minwidth=40, anchor='center')
        self.tree.column('Статус', width=110, minwidth=100)
        self.tree.column('Месяц', width=110, minwidth=100)
        self.tree.column('Тип', width=120, minwidth=100)
        self.tree.column('Спорт', width=150, minwidth=120)
        self.tree.column('Название', width=250, minwidth=200)
        self.tree.column('Место', width=180, minwidth=150)
        self.tree.column('Сумма на детей', width=140, minwidth=120)
        self.tree.column('Тренеры', width=160, minwidth=130)
        self.tree.column('Изменено', width=140, minwidth=120)
        
        # Прокрутка
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Двойной клик для редактирования (только на строке данных, не на заголовке)
        def on_double_click(event):
            # Проверяем что клик был по строке, а не по заголовку или пустому месту
            region = self.tree.identify_region(event.x, event.y)
            if region == "cell":
                item = self.tree.identify_row(event.y)
                if item:  # Если есть выбранная строка
                    self._edit_event()
        
        #self.tree.bind('<Double-1>', on_double_click)
        
        # Одиночный клик по звездочке для избранного
        self.tree.bind('<Button-1>', self._on_tree_click)
        
        # Строка состояния - современный дизайн
        status_frame = tk.Frame(self.root, bg=self.colors['primary'], height=35)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="Готово к работе")
        status_bar = tk.Label(
            status_frame, 
            textvariable=self.status_var,
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=(FONT_FAMILY, 9),
            anchor='w',
            padx=15
        )
        status_bar.pack(fill=tk.BOTH, expand=True)
    
    def _on_year_change(self):
        """Обработчик изменения года"""
        self._update_dashboard()
        self._load_events()
    
    def _reset_filters(self):
        """Сбросить все фильтры"""
        self.sport_filter_var.set("Все")
        self.month_filter_var.set("Все")
        if hasattr(self, 'quick_filter_var'):
            self.quick_filter_var.set("Все")
        self._load_events()
    
    def _load_events(self):
        """Загрузить мероприятия из БД с учетом фильтров"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получаем мероприятия за выбранный год
        year = self.selected_year.get()
        events_data = self.db.get_events_by_year(year)
        
        if not events_data:
            self.status_var.set(f"Нет мероприятий на {year} год")
            return
        
        # Получаем значения фильтров
        sport_filter = self.sport_filter_var.get()
        month_filter = self.month_filter_var.get()
        search_query = self.search_var.get().lower().strip()
        quick_filter = self.quick_filter_var.get() if hasattr(self, 'quick_filter_var') else "Все"
        
        # Применяем фильтры
        filtered_count = 0
        events_list = []  # Для сортировки
        
        for row in events_data:
            event = Event.from_db_row(row)
            
            # Быстрые фильтры
            if quick_filter == "Проведённые" and event.status != "Проведено":
                continue
            elif quick_filter == "Запланированные" and event.status not in ("Запланировано", None):
                continue
            elif quick_filter == "Отменённые" and event.status != "Отменено":
                continue
            elif quick_filter == "Внутренние" and event.event_type != "Внутреннее":
                continue
            elif quick_filter == "Выездные" and event.event_type != "Выездное":
                continue
            elif quick_filter == "Избранные" and not event.is_favorite:
                continue
            
            # Фильтр по виду спорта
            if sport_filter != "Все" and event.sport != sport_filter:
                continue
            
            # Фильтр по месяцу
            if month_filter != "Все" and event.month != month_filter:
                continue
            
            # Поиск по названию, месту, примечаниям
            if search_query:
                searchable_text = f"{event.name} {event.location} {event.notes or ''}".lower()
                if search_query not in searchable_text:
                    continue
            
            events_list.append(event)
        
        # Сортировка если нужно
        if self.sort_column:
            events_list = self._apply_sorting(events_list)
        
        # Вставляем в таблицу
        for event in events_list:
            # Обрезаем название если слишком длинное
            name = event.name if len(event.name) <= 50 else event.name[:47] + "..."
            
            status = event.status or "Запланировано"
            
            # Звёздочка для избранного
            favorite_mark = "★" if event.is_favorite else "☆"
            
            # Формируем информацию о тренерах
            trainers_info = ""
            if event.trainers_list:
                trainers_info = f"{len(event.trainers_list)} чел."
            else:
                trainers_info = f"{event.trainers_count} чел."
            
            # Дата последнего изменения
            modified = ""
            if event.last_modified:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(event.last_modified)
                    modified = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    modified = "-"
            else:
                modified = "-"
            
            # Вставляем строку
            item_id = self.tree.insert('', tk.END, values=(
                favorite_mark,
                status,
                event.month,
                event.event_type,
                event.sport,
                name,
                event.location,
                format_rubles_compact(event.children_budget),
                trainers_info,
                modified
            ), tags=(str(event.id),))
            
            # Цветовая индикация по статусу
            if status == "Проведено":
                self.tree.tag_configure(f"status_{item_id}", background='#D4EDDA', foreground='#155724')  # Зелёный
            elif status == "Отменено":
                self.tree.tag_configure(f"status_{item_id}", background='#F8D7DA', foreground='#721C24')  # Красный
            elif status == "Перенесено":
                self.tree.tag_configure(f"status_{item_id}", background='#FFF3CD', foreground='#856404')  # Жёлтый
            else:  # Запланировано
                self.tree.tag_configure(f"status_{item_id}", background='#D1ECF1', foreground='#0C5460')  # Голубой
            
            # Применяем тег
            self.tree.item(item_id, tags=(str(event.id), f"status_{item_id}"))
            
            filtered_count += 1
        
        # Обновляем статус с информацией о фильтрах
        filter_info = []
        if sport_filter != "Все":
            filter_info.append(f"🏅 {sport_filter}")
        if month_filter != "Все":
            filter_info.append(f"📅 {month_filter}")
        if search_query:
            filter_info.append(f"🔍 \"{search_query}\"")
        
        if filter_info:
            status_text = f"Показано: {filtered_count} из {len(events_data)} | Активные фильтры: {' | '.join(filter_info)}"
        else:
            status_text = f"Всего мероприятий: {filtered_count} на {year} год"
        
        self.status_var.set(status_text)
    
    def _reload_all(self):
        """Перезагрузить данные и обновить дашборд"""
        self._update_dashboard()
        self._load_events()
    
    def _add_event(self):
        """Добавить новое мероприятие"""
        year = self.selected_year.get()
        AddEventWindow(self.root, self.db, year, callback=self._reload_all)
    
    def _edit_event(self):
        """Редактировать выбранное мероприятие"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите мероприятие для редактирования")
            return
        
        # Получаем ID мероприятия
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        event_id = int(tags[0])
        
        # Получаем данные мероприятия из БД
        event_data = self.db.get_event_by_id(event_id)
        if not event_data:
            messagebox.showerror("Ошибка", "Мероприятие не найдено")
            return
        
        event = Event.from_db_row(event_data)
        year = self.selected_year.get()
        AddEventWindow(self.root, self.db, year, callback=self._reload_all, event=event)
    
    def _clarify_event(self):
        """Уточнить детали выбранного мероприятия"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите мероприятие для уточнения")
            return
        
        # Получаем ID мероприятия
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        event_id = int(tags[0])
        
        # Получаем данные мероприятия из БД
        event_data = self.db.get_event_by_id(event_id)
        if not event_data:
            messagebox.showerror("Ошибка", "Мероприятие не найдено")
            return
        
        event = Event.from_db_row(event_data)
        ClarifyEventWindow(self.root, self.db, event, callback=self._reload_all)
    
    def _manage_estimates(self):
        """Открыть окно управления сметами для выбранного мероприятия"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите мероприятие для создания смет")
            return
        
        # Получаем ID мероприятия
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        event_id = int(tags[0])
        
        # Получаем данные мероприятия из БД
        event_data = self.db.get_event_by_id(event_id)
        if not event_data:
            messagebox.showerror("Ошибка", "Мероприятие не найдено")
            return
        
        event = Event.from_db_row(event_data)
        
        # Открываем окно управления сметами
        EstimateWindow(self.root, self.db, event)
    
    def _delete_event(self):
        """Удалить выбранное мероприятие"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите мероприятие для удаления")
            return
        
        # Подтверждение
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить мероприятие?"):
            return
        
        # Получаем ID мероприятия
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        event_id = int(tags[0])
        
        try:
            self.db.delete_event(event_id)
            self._reload_all()
            messagebox.showinfo("Успешно", "Мероприятие удалено")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить мероприятие: {str(e)}")
    
    def _import_from_csv(self):
        """Импортировать мероприятия из CSV"""
        year = self.selected_year.get()
        ImportCSVWindow(self.root, self.db, year, callback=self._reload_all)
    
    def _export_to_csv(self):
        """Экспортировать календарный план в CSV"""
        year = self.selected_year.get()
        events_data = self.db.get_events_by_year(year)
        
        if not events_data:
            messagebox.showinfo("Информация", f"Нет мероприятий на {year} год для экспорта")
            return
        
        # Диалог сохранения файла
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile=f"Календарный_план_{year}.csv"
        )
        
        if not file_path:
            return  # Пользователь отменил сохранение
        
        try:
            # Преобразуем в объекты Event
            events = [Event.from_db_row(row) for row in events_data]
            
            # Открываем файл для записи с кодировкой UTF-8-BOM (для корректного отображения в Excel)
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Определяем заголовки
                fieldnames = [
                    'Месяц', 'Тип', 'Вид спорта', 'Статус', 'Название', 
                    'Место проведения', 'Дата начала', 'Дата окончания',
                    'План: Сумма на детей', 'Факт: Сумма на детей',
                    'Количество тренеров', 'План: Сумма на тренеров', 
                    'Факт: Сумма на тренеров', 'Примечания', 
                    'Причина отмены', 'Причина переноса'
                ]
                
                # Используем точку с запятой как разделитель для русской версии Excel
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                # Записываем данные
                for event in events:
                    writer.writerow({
                        'Месяц': event.month,
                        'Тип': event.event_type,
                        'Вид спорта': event.sport,
                        'Статус': event.status or 'Запланировано',
                        'Название': event.name,
                        'Место проведения': event.location,
                        'Дата начала': event.actual_start_date or '',
                        'Дата окончания': event.actual_end_date or '',
                        'План: Сумма на детей': event.children_budget,
                        'Факт: Сумма на детей': event.actual_children_budget if event.actual_children_budget is not None else '',
                        'Количество тренеров': event.trainers_count,
                        'План: Сумма на тренеров': event.trainers_budget,
                        'Факт: Сумма на тренеров': event.actual_trainers_budget if event.actual_trainers_budget is not None else '',
                        'Примечания': event.notes or '',
                        'Причина отмены': event.cancellation_reason or '',
                        'Причина переноса': event.postponement_reason or ''
                    })
            
            messagebox.showinfo("Успешно", f"Календарный план экспортирован в:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать файл:\n{str(e)}")
    
    def _view_plan(self):
        """Открыть окно просмотра плана"""
        year = self.selected_year.get()
        events_data = self.db.get_events_by_year(year)
        
        if not events_data:
            messagebox.showinfo("Информация", f"Нет мероприятий на {year} год")
            return
        
        ViewPlanWindow(self.root, self.db, year)
    
    def _open_report_direct(self, report_type: str):
        """
        Открыть окно с конкретным типом отчёта
        
        Args:
            report_type: Тип отчёта (by_sport, by_month, by_event_type, by_status, by_trainers, by_type)
        """
        year = self.selected_year.get()
        events_data = self.db.get_events_by_year(year)
        
        if not events_data:
            messagebox.showinfo("Информация", f"Нет мероприятий на {year} год")
            return
        
        ViewPlanWindow(self.root, self.db, year, initial_report_type=report_type)
    
    def _check_data(self):
        """Открыть окно проверки целостности данных"""
        year = self.selected_year.get()
        DataCheckWindow(self.root, self.db, year)
    
    def _duplicate_event(self):
        """Дублировать выбранное мероприятие"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("Внимание", "Выберите мероприятие для дублирования")
            return
        
        # Получаем ID события
        item = selection[0]
        event_id = int(self.tree.item(item, 'tags')[0])
        
        # Получаем событие из БД
        event_data = self.db.get_event_by_id(event_id)
        if not event_data:
            messagebox.showerror("Ошибка", "Мероприятие не найдено")
            return
        
        event = Event.from_db_row(event_data)
        
        # Открываем окно добавления с данными текущего события
        # но меняем название чтобы было понятно что это копия
        event.name = f"{event.name} (копия)"
        event.id = None  # Сбрасываем ID чтобы создалось новое
        
        AddEventWindow(self.root, self.db, event.year, self._reload_all, event)
    
    def _open_backup_window(self):
        """Открыть окно управления резервными копиями"""
        BackupWindow(self.root)
    
    def _auto_backup(self):
        """Автоматическое резервное копирование (раз в день)"""
        import os
        from datetime import date
        
        # Проверяем есть ли сегодняшний бэкап
        backups = self.backup_manager.get_backups()
        today = date.today().strftime("%Y%m%d")
        
        has_today_backup = any(today in backup[0] for backup in backups)
        
        if not has_today_backup:
            success, message = self.backup_manager.create_backup()
            if success:
                print(f"Автоматический бэкап создан: {message}")
            
            # Очищаем старые бэкапы (оставляем последние 10)
            self.backup_manager.cleanup_old_backups(keep_count=10)
    
    def _setup_hotkeys(self):
        """Настроить горячие клавиши"""
        # Ctrl+N - новое мероприятие
        self.root.bind('<Control-n>', lambda e: self._add_event())
        self.root.bind('<Control-N>', lambda e: self._add_event())
        
        # Ctrl+E - редактировать
        self.root.bind('<Control-e>', lambda e: self._edit_event())
        self.root.bind('<Control-E>', lambda e: self._edit_event())
        
        # Ctrl+D - дублировать (вместо Delete чтобы не путать)
        self.root.bind('<Control-d>', lambda e: self._duplicate_event())
        self.root.bind('<Control-D>', lambda e: self._duplicate_event())
        
        # Delete - удалить
        self.root.bind('<Delete>', lambda e: self._delete_event())
        
        # Ctrl+F - фокус на поиск
        def focus_search(e):
            # Находим виджет поиска и ставим фокус
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry) and child.cget('textvariable') == str(self.search_var):
                            child.focus_set()
                            child.select_range(0, tk.END)
                            return
        
        self.root.bind('<Control-f>', focus_search)
        self.root.bind('<Control-F>', focus_search)
        
        # F5 - обновить
        self.root.bind('<F5>', lambda e: self._load_events())
        
        # Escape - очистить поиск
        self.root.bind('<Escape>', lambda e: self.search_var.set(''))
    
    def _sort_by_column(self, column):
        """Сортировать таблицу по колонке"""
        # Если клик по той же колонке - меняем направление
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Перезагружаем данные с сортировкой
        self._load_events()
    
    def _apply_sorting(self, events_list):
        """Применить сортировку к списку событий"""
        column = self.sort_column
        reverse = self.sort_reverse
        
        # Определяем ключ сортировки
        if column == 'Статус':
            key_func = lambda e: e.status or "Запланировано"
        elif column == 'Месяц':
            # Сортируем по индексу месяца
            key_func = lambda e: MONTHS.index(e.month) if e.month in MONTHS else 999
        elif column == 'Тип':
            key_func = lambda e: e.event_type
        elif column == 'Спорт':
            key_func = lambda e: e.sport
        elif column == 'Название':
            key_func = lambda e: e.name
        elif column == 'Место':
            key_func = lambda e: e.location
        elif column == 'Сумма на детей':
            key_func = lambda e: e.children_budget
        elif column == 'Тренеров':
            key_func = lambda e: e.trainers_count
        elif column == 'Сумма на тренеров':
            key_func = lambda e: e.trainers_budget
        else:
            return events_list
        
        return sorted(events_list, key=key_func, reverse=reverse)
    
    def _apply_sport_filter(self, sport):
        """Применить фильтр по виду спорта из меню"""
        self.sport_filter_var.set(sport)
        self._load_events()
    
    def _apply_month_filter(self, month):
        """Применить фильтр по месяцу из меню"""
        self.month_filter_var.set(month)
        self._load_events()
    
    def _show_hotkeys_help(self):
        """Показать окно с горячими клавишами"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Горячие клавиши")
        help_window.geometry("500x450")
        help_window.transient(self.root)
        
        # Обработчик закрытия окна (для Red OS и других систем)
        help_window.protocol("WM_DELETE_WINDOW", help_window.destroy)
        
        # Заголовок
        header = ttk.Label(
            help_window,
            text="⌨️ Горячие клавиши",
            font=(FONT_FAMILY, 14, 'bold')
        )
        header.pack(pady=10)
        
        # Текст с горячими клавишами
        text = tk.Text(help_window, wrap=tk.WORD, width=60, height=20, font=(MONOSPACE_FONT, 10))
        text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        hotkeys_text = """
РАБОТА С МЕРОПРИЯТИЯМИ:
  Ctrl+N        Создать новое мероприятие
  Ctrl+E        Редактировать выбранное мероприятие
  Ctrl+D        Дублировать выбранное мероприятие
  Delete        Удалить выбранное мероприятие
  
ПОИСК И НАВИГАЦИЯ:
  Ctrl+F        Перейти к строке поиска
  Escape        Очистить строку поиска
  F5            Обновить список мероприятий
  
РАБОТА С ТАБЛИЦЕЙ:
  Click         Клик по заголовку колонки - сортировка
  Click на ★    Добавить/убрать из избранного
  
ОБЩЕЕ:
  Alt+F4        Выход из программы
  
СОВЕТ: Используйте горячие клавиши для ускорения работы!
        """
        
        text.insert('1.0', hotkeys_text)
        text.config(state='disabled')
        
        # Кнопка закрытия
        ttk.Button(help_window, text="Закрыть", command=help_window.destroy).pack(pady=10)
    
    def _show_new_features(self):
        """Показать окно с новыми функциями"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Новые функции")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        
        # Обработчик закрытия окна (для Red OS и других систем)
        help_window.protocol("WM_DELETE_WINDOW", help_window.destroy)
        
        # Заголовок
        header = ttk.Label(
            help_window,
            text="✨ Новые функции программы",
            font=(FONT_FAMILY, 14, 'bold')
        )
        header.pack(pady=10)
        
        # Текст с описанием
        text = tk.Text(help_window, wrap=tk.WORD, width=70, height=22, font=(FONT_FAMILY, 10))
        text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        features_text = """
1. 💾 РЕЗЕРВНОЕ КОПИРОВАНИЕ
   • Автоматические бэкапы при запуске (раз в день)
   • Ручное создание и восстановление копий
   • Папка: backups/

2. 🔍 БЫСТРЫЙ ПОИСК
   • Поиск по названию, месту, примечаниям
   • Обновление результатов при вводе
   • Работает вместе с фильтрами

3. ⌨️ ГОРЯЧИЕ КЛАВИШИ
   • Ctrl+N, Ctrl+E, Ctrl+D, Delete
   • Ctrl+F для поиска, F5 для обновления
   • Смотрите полный список в "Справка → Горячие клавиши"

4. 📋 ДУБЛИРОВАНИЕ МЕРОПРИЯТИЙ
   • Быстрое создание похожих мероприятий
   • Кнопка "Дублировать" или Ctrl+D
   • Автоматически добавляется "(копия)" к названию

5. 📊 СОРТИРОВКА В ТАБЛИЦЕ
   • Клик по заголовку колонки для сортировки
   • Повторный клик меняет направление
   • Значки ▲▼ показывают возможность сортировки

6. 📑 МЕНЮ ПРИЛОЖЕНИЯ
   • Все функции доступны через меню
   • Фильтры по спортам и месяцам
   • Быстрый доступ к любой функции

СОВЕТ: Подробнее в файле "НОВЫЕ_ФУНКЦИИ.md"
        """
        
        text.insert('1.0', features_text)
        text.config(state='disabled')
        
        # Кнопка закрытия
        ttk.Button(help_window, text="Закрыть", command=help_window.destroy).pack(pady=10)
    
    def _show_about(self):
        """Показать окно "О программе" """
        messagebox.showinfo(
            "О программе",
            "ДЮСК Ямбург\n"
            "Календарные планы спортивных мероприятий\n\n"
            "Версия: 2.0\n"
            "Год: 2025\n\n"
            "ООО \"Газпром добыча Ямбург\"\n"
            "филиал Управление по эксплуатации вахтовых посёлков\n"
            "Детско-юношеский спортивный клуб \"Ямбург\"\n\n"
            "Возможности:\n"
            "• Управление мероприятиями\n"
            "• Фильтрация и поиск\n"
            "• 5 типов отчётов (TXT, CSV, HTML)\n"
            "• Импорт/экспорт данных\n"
            "• Резервное копирование\n"
            "• Горячие клавиши для быстрой работы\n"
            "• Автоматическое открытие HTML отчётов\n\n"
            "Python 3.8.20 • SQLite3 • Tkinter"
        )
    
    def _create_dashboard(self):
        """Создать дашборд со статистикой"""
        dashboard_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], relief='solid', bd=1)
        dashboard_frame.pack(fill=tk.X, padx=15, pady=(5, 10))
        
        # Заголовок (без иконки для совместимости с Red OS)
        title_label = tk.Label(
            dashboard_frame,
            text="Статистика",
            bg=self.colors['bg_dark'],
            fg=self.colors['primary'],
            font=(FONT_FAMILY, 11, 'bold')
        )
        title_label.pack(anchor='w', padx=10, pady=(8, 5))
        
        # Контейнер для карточек статистики
        cards_frame = tk.Frame(dashboard_frame, bg=self.colors['bg_dark'])
        cards_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Карточки со статистикой (без иконок для совместимости с Red OS)
        self.dashboard_vars = {}
        metrics = [
            ("total", "Всего", "", self.colors['primary']),
            ("completed", "Проведено", "", "#28a745"),
            ("planned", "Запланировано", "", "#17a2b8"),
            ("cancelled", "Отменено", "", "#dc3545"),
            ("children_budget", "Бюджет детей", "", self.colors['primary_dark']),
            ("trainers_budget", "Бюджет тренеров", "", self.colors['primary_light'])
        ]
        
        for key, label, icon, color in metrics:
            self.dashboard_vars[key] = tk.StringVar(value="0")
            self._create_stat_card(cards_frame, icon, label, self.dashboard_vars[key], color)
        
        # Сразу обновляем статистику
        self._update_dashboard()
    
    def _create_stat_card(self, parent, icon, label, var, color):
        """Создать карточку со статистикой"""
        card = tk.Frame(parent, bg=self.colors['white'], relief='raised', bd=1)
        card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        
        # Иконка - только если не пустая (для совместимости с Red OS)
        if icon:
            icon_label = tk.Label(
                card,
                text=icon,
                bg=self.colors['white'],
                font=(FONT_FAMILY, 20)
            )
            icon_label.pack(pady=(8, 0))
        
        value_label = tk.Label(
            card,
            textvariable=var,
            bg=self.colors['white'],
            fg=color,
            font=(FONT_FAMILY, 16, 'bold')
        )
        value_label.pack()
        
        text_label = tk.Label(
            card,
            text=label,
            bg=self.colors['white'],
            fg=self.colors['text_light'],
            font=(FONT_FAMILY, 9)
        )
        text_label.pack(pady=(0, 8))
    
    def _update_dashboard(self):
        """Обновить статистику на дашборде"""
        year = self.selected_year.get()
        events_data = self.db.get_events_by_year(year)
        
        if not events_data:
            for key in self.dashboard_vars:
                self.dashboard_vars[key].set("0")
            return
        
        total = len(events_data)
        completed = sum(1 for row in events_data if row[11] == "Проведено")
        planned = sum(1 for row in events_data if row[11] in ("Запланировано", None))
        cancelled = sum(1 for row in events_data if row[11] == "Отменено")
        
        children_budget = sum(row[7] for row in events_data)
        trainers_budget = sum(row[9] for row in events_data)
        
        self.dashboard_vars["total"].set(str(total))
        self.dashboard_vars["completed"].set(str(completed))
        self.dashboard_vars["planned"].set(str(planned))
        self.dashboard_vars["cancelled"].set(str(cancelled))
        self.dashboard_vars["children_budget"].set(format_rubles(children_budget))
        self.dashboard_vars["trainers_budget"].set(format_rubles(trainers_budget))
    
    def _create_quick_filters(self):
        """Создать панель быстрых фильтров"""
        filters_frame = tk.Frame(self.root, bg=self.colors['bg'], relief='flat')
        filters_frame.pack(fill=tk.X, padx=15, pady=(0, 5))
        
        # Заголовок (без иконки для совместимости с Red OS)
        tk.Label(
            filters_frame,
            text="Быстрые фильтры:",
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=(FONT_FAMILY, 10, 'bold')
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Переменная для хранения активного быстрого фильтра
        self.quick_filter_var = tk.StringVar(value="Все")
        
        # Кнопки фильтров (без иконок для совместимости с Red OS)
        quick_filters = [
            "Все",
            "Проведённые",
            "Запланированные",
            "Отменённые",
            "Внутренние",
            "Выездные",
            "Избранные"
        ]
        
        for filter_name in quick_filters:
            btn = tk.Button(
                filters_frame,
                text=filter_name,
                command=lambda f=filter_name: self._apply_quick_filter(f),
                bg=self.colors['white'],
                fg=self.colors['text'],
                font=(FONT_FAMILY, 9),
                relief='raised',
                cursor='hand2',
                padx=10,
                pady=5,
                bd=1
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            # Hover эффект
            def make_filter_hover(button):
                def on_enter(e):
                    button['bg'] = self.colors['primary_light']
                    button['fg'] = self.colors['white']
                def on_leave(e):
                    button['bg'] = self.colors['white']
                    button['fg'] = self.colors['text']
                button.bind('<Enter>', on_enter)
                button.bind('<Leave>', on_leave)
            
            make_filter_hover(btn)
    
    def _apply_quick_filter(self, filter_name):
        """Применить быстрый фильтр"""
        self.quick_filter_var.set(filter_name)
        
        # Сбрасываем другие фильтры
        if filter_name == "Все":
            self.sport_filter_var.set("Все")
            self.month_filter_var.set("Все")
        elif filter_name == "Внутренние" or filter_name == "Выездные":
            # Фильтр по типу мероприятия - обрабатываем в _load_events
            pass
        
        self._load_events()
    
    def _on_tree_click(self, event):
        """Обработчик клика по таблице (для избранного)"""
        # Определяем, по какой колонке кликнули
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        # Если кликнули по первой колонке (★) и есть выбранная строка
        if column == "#1" and item:  # #1 это первая колонка
            # Получаем ID мероприятия из тега
            tags = self.tree.item(item, 'tags')
            if tags:
                event_id = int(tags[0])
                
                # Переключаем избранное в БД
                self.db.toggle_favorite(event_id)
                
                # Перезагружаем таблицу
                self._load_events()
                self._update_dashboard()
    
    def _on_close(self):
        """Обработчик закрытия главного окна"""
        # Закрываем БД
        if hasattr(self, 'db'):
            self.db.close()
        # Закрываем приложение
        self.root.quit()
    
    def run(self):
        """Запустить главный цикл приложения"""
        self.root.mainloop()
    
    def __del__(self):
        """Деструктор - закрываем БД"""
        if hasattr(self, 'db'):
            self.db.close()

