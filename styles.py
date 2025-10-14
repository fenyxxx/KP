# -*- coding: utf-8 -*-
"""
Общие стили для всех окон программы
"""

import tkinter as tk
from tkinter import ttk
import platform


def get_font_family():
    """
    Определить подходящее семейство шрифтов для текущей ОС
    
    Returns:
        str: Название шрифта
    """
    system = platform.system()
    
    if system == 'Windows':
        return 'Segoe UI'
    elif system == 'Darwin':  # macOS
        return 'SF Pro Display'
    else:  # Linux (включая Red OS)
        # Проверяем доступные шрифты
        try:
            import tkinter.font as tkfont
            available_fonts = tkfont.families()
            
            # Предпочитаемые шрифты для Linux в порядке приоритета
            preferred_fonts = [
                'DejaVu Sans',
                'Liberation Sans', 
                'Ubuntu',
                'Noto Sans',
                'FreeSans',
                'Helvetica',
                'Arial'
            ]
            
            for font in preferred_fonts:
                if font in available_fonts:
                    return font
        except:
            pass
        
        # Fallback на системный шрифт
        return 'TkDefaultFont'


def get_monospace_font():
    """
    Определить подходящий моноширинный шрифт для текущей ОС
    
    Returns:
        str: Название моноширинного шрифта
    """
    system = platform.system()
    
    if system == 'Windows':
        return 'Courier New'
    elif system == 'Darwin':  # macOS
        return 'Monaco'
    else:  # Linux (включая Red OS)
        try:
            import tkinter.font as tkfont
            available_fonts = tkfont.families()
            
            preferred_fonts = [
                'DejaVu Sans Mono',
                'Liberation Mono',
                'Ubuntu Mono',
                'Noto Mono',
                'FreeMono',
                'Courier'
            ]
            
            for font in preferred_fonts:
                if font in available_fonts:
                    return font
        except:
            pass
        
        return 'TkFixedFont'


# Определяем шрифты для текущей системы
FONT_FAMILY = get_font_family()
MONOSPACE_FONT = get_monospace_font()


# Корпоративные цвета ПАО Газпром
COLORS = {
    'primary': '#0066B3',        # Синий Газпром
    'primary_dark': '#004B87',    # Тёмно-синий
    'primary_light': '#3399CC',   # Светло-синий
    'accent': '#FF6B00',          # Оранжевый акцент
    'bg': '#F5F7FA',              # Светлый фон
    'bg_dark': '#E8EEF4',         # Тёмный фон
    'text': '#2C3E50',            # Тёмный текст
    'text_light': '#7F8C8D',      # Светлый текст
    'white': '#FFFFFF',
    'border': '#BDC3C7',
    'table_header': '#87CEEB',    # Голубой для заголовков таблиц
    'table_header_active': '#5DADE2'  # Яркий голубой при наведении
}


def apply_styles(window):
    """
    Применить единые стили к окну
    
    Args:
        window: Окно tk.Toplevel или tk.Tk
    """
    # Фон окна
    window.configure(bg=COLORS['bg'])
    
    # Создаём стиль
    style = ttk.Style()
    
    # Пытаемся использовать тему clam (лучше работает с цветами)
    try:
        style.theme_use('clam')
    except:
        pass
    
    # Стили для Frame
    style.configure('TFrame', background=COLORS['bg'])
    
    # Стили для Label
    style.configure('TLabel',
                   background=COLORS['bg'],
                   foreground=COLORS['text'],
                   font=(FONT_FAMILY, 10))
    
    # Заголовки
    style.configure('Header.TLabel',
                   background=COLORS['bg'],
                   foreground=COLORS['primary'],
                   font=(FONT_FAMILY, 14, 'bold'))
    
    # Стили для Button
    style.configure('TButton',
                   font=(FONT_FAMILY, 10),
                   padding=8)
    
    # Синяя кнопка (акцент)
    style.configure('Primary.TButton',
                   font=(FONT_FAMILY, 10, 'bold'))
    
    # Стили для Combobox
    style.configure('TCombobox',
                   font=(FONT_FAMILY, 10))
    
    # Стили для Entry
    style.configure('TEntry',
                   font=(FONT_FAMILY, 10))
    
    # Стили для Checkbutton
    style.configure('TCheckbutton',
                   background=COLORS['bg'],
                   foreground=COLORS['text'],
                   font=(FONT_FAMILY, 10))
    
    # Стили для Radiobutton
    style.configure('TRadiobutton',
                   background=COLORS['bg'],
                   foreground=COLORS['text'],
                   font=(FONT_FAMILY, 10))


def create_styled_button(parent, text, command, style='normal'):
    """
    Создать кнопку в едином стиле
    
    Args:
        parent: Родительский виджет
        text: Текст кнопки
        command: Команда при нажатии
        style: Стиль кнопки ('primary', 'secondary', 'accent', 'normal')
    
    Returns:
        tk.Button: Стилизованная кнопка
    """
    if style == 'primary':
        bg = COLORS['primary']
        fg = COLORS['white']
        hover_bg = COLORS['primary_dark']
        font_style = (FONT_FAMILY, 10, 'bold')
    elif style == 'accent':
        bg = COLORS['accent']
        fg = COLORS['white']
        hover_bg = '#E55D00'
        font_style = (FONT_FAMILY, 10, 'bold')
    elif style == 'secondary':
        bg = COLORS['primary_light']
        fg = COLORS['white']
        hover_bg = COLORS['primary']
        font_style = (FONT_FAMILY, 10)
    else:  # normal
        bg = COLORS['bg_dark']
        fg = COLORS['text']
        hover_bg = COLORS['border']
        font_style = (FONT_FAMILY, 10)
    
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=font_style,
        relief='flat',
        cursor='hand2',
        padx=15,
        pady=8,
        activebackground=hover_bg,
        activeforeground=fg if style in ['primary', 'accent', 'secondary'] else COLORS['text']
    )
    
    # Hover эффект
    def on_enter(e):
        button['bg'] = hover_bg
    
    def on_leave(e):
        button['bg'] = bg
    
    button.bind('<Enter>', on_enter)
    button.bind('<Leave>', on_leave)
    
    return button


def create_styled_entry(parent, textvariable=None, width=None):
    """
    Создать поле ввода в едином стиле
    
    Args:
        parent: Родительский виджет
        textvariable: Переменная для текста
        width: Ширина поля
    
    Returns:
        tk.Entry: Стилизованное поле ввода
    """
    frame = tk.Frame(parent, bg=COLORS['white'], relief='solid', bd=1)
    
    entry = tk.Entry(
        frame,
        textvariable=textvariable,
        font=(FONT_FAMILY, 10),
        bg=COLORS['white'],
        fg=COLORS['text'],
        relief='flat',
        bd=0
    )
    
    if width:
        entry.config(width=width)
    
    entry.pack(padx=8, pady=6, fill=tk.X, expand=True)
    
    return frame, entry


def create_styled_label(parent, text, style='normal'):
    """
    Создать метку в едином стиле
    
    Args:
        parent: Родительский виджет
        text: Текст метки
        style: Стиль ('normal', 'header', 'hint')
    
    Returns:
        ttk.Label: Стилизованная метка
    """
    if style == 'header':
        return ttk.Label(parent, text=text, style='Header.TLabel')
    elif style == 'hint':
        return ttk.Label(parent, text=text, font=(FONT_FAMILY, 8), foreground=COLORS['text_light'])
    else:
        return ttk.Label(parent, text=text)

