# -*- coding: utf-8 -*-
"""
Окно проверки целостности данных
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from data_validator import DataValidator
from styles import apply_styles, COLORS, create_styled_button


class DataCheckWindow:
    """Класс окна проверки целостности данных"""
    
    def __init__(self, parent, db, year):
        """
        Инициализация окна
        
        Args:
            parent: Родительское окно
            db: Объект базы данных
            year: Год для проверки
        """
        self.db = db
        self.year = year
        self.validator = DataValidator(db)
        
        # Создаём окно
        self.window = tk.Toplevel(parent)
        self.window.title(f"ДЮСК Ямбург - Проверка данных за {year} год")
        self.window.geometry("900x700")
        self.window.transient(parent)
        
        # Применяем единый стиль
        apply_styles(self.window)
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._create_widgets()
        self._run_check()
    
    def _create_widgets(self):
        """Создать виджеты окна"""
        # Заголовок
        header_frame = ttk.Frame(self.window, padding="15")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text=f"🔍 Проверка целостности данных за {self.year} год",
            style='Header.TLabel'
        ).pack(anchor='w')
        
        # Область с результатами
        content_frame = ttk.Frame(self.window, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Резюме
        summary_frame = tk.Frame(content_frame, bg=COLORS['bg_dark'], relief='solid', bd=1)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            summary_frame,
            text="📊 Резюме проверки:",
            font=('Segoe UI', 11, 'bold'),
            background=COLORS['bg_dark']
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        self.summary_text = tk.Text(
            summary_frame,
            height=5,
            font=('Segoe UI', 10),
            bg=COLORS['white'],
            wrap=tk.WORD,
            relief='flat'
        )
        self.summary_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Детали проблем
        ttk.Label(
            content_frame,
            text="📋 Детальный список проблем:",
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w', pady=(10, 5))
        
        # Текстовое поле с деталями
        details_frame = ttk.Frame(content_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            font=('Segoe UI', 9),
            wrap=tk.WORD,
            bg=COLORS['white']
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        button_frame = ttk.Frame(self.window, padding="15")
        button_frame.pack(fill=tk.X)
        
        create_styled_button(
            button_frame,
            "🔄 Повторить проверку",
            self._run_check,
            'secondary'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "💾 Сохранить отчёт",
            self._save_report,
            'primary'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "Закрыть",
            self.window.destroy,
            'normal'
        ).pack(side=tk.RIGHT, padx=5)
    
    def _run_check(self):
        """Запустить проверку данных"""
        # Очищаем поля
        self.summary_text.delete('1.0', tk.END)
        self.details_text.delete('1.0', tk.END)
        
        # Выполняем проверку
        results = self.validator.check_all(self.year)
        
        # Выводим резюме
        summary = self.validator.get_summary(results)
        self.summary_text.insert('1.0', summary)
        self.summary_text.config(state='disabled')
        
        # Выводим детали
        total_issues = sum(len(issues) for issues in results.values())
        
        if total_issues == 0:
            self.details_text.insert('1.0', "Отлично! Все данные в порядке. Проблем не обнаружено.")
            self.details_text.config(state='disabled')
            return
        
        details = ""
        issue_num = 1
        
        # Мероприятия без бюджета
        if results['zero_total_budget']:
            details += "═" * 80 + "\n"
            details += "❌ МЕРОПРИЯТИЯ БЕЗ БЮДЖЕТА\n"
            details += "═" * 80 + "\n\n"
            for issue in results['zero_total_budget']:
                details += f"{issue_num}. {issue['name']}\n"
                details += f"   Месяц: {issue['month']}\n"
                details += f"   Проблема: {issue['issue']}\n"
                details += f"   ID: {issue['id']}\n\n"
                issue_num += 1
        
        # Проведённые без дат
        if results['no_actual_dates']:
            details += "═" * 80 + "\n"
            details += "📅 ПРОВЕДЁННЫЕ МЕРОПРИЯТИЯ БЕЗ ФАКТИЧЕСКИХ ДАТ\n"
            details += "═" * 80 + "\n\n"
            for issue in results['no_actual_dates']:
                details += f"{issue_num}. {issue['name']}\n"
                details += f"   Месяц: {issue['month']}\n"
                details += f"   Проблема: {issue['issue']}\n"
                details += f"   ID: {issue['id']}\n\n"
                issue_num += 1
        
        # Отменённые без причины
        if results['no_cancellation_reason']:
            details += "═" * 80 + "\n"
            details += "📝 ОТМЕНЁННЫЕ МЕРОПРИЯТИЯ БЕЗ ПРИЧИНЫ\n"
            details += "═" * 80 + "\n\n"
            for issue in results['no_cancellation_reason']:
                details += f"{issue_num}. {issue['name']}\n"
                details += f"   Месяц: {issue['month']}\n"
                details += f"   Проблема: {issue['issue']}\n"
                details += f"   ID: {issue['id']}\n\n"
                issue_num += 1
        
        # Подозрительные расходы
        if results['suspicious_budget']:
            details += "═" * 80 + "\n"
            details += "💰 ПОДОЗРИТЕЛЬНЫЕ ФАКТИЧЕСКИЕ РАСХОДЫ\n"
            details += "═" * 80 + "\n\n"
            for issue in results['suspicious_budget']:
                details += f"{issue_num}. {issue['name']}\n"
                details += f"   Месяц: {issue['month']}\n"
                details += f"   Проблема: {issue['issue']}\n"
                details += f"   ID: {issue['id']}\n\n"
                issue_num += 1
        
        # Выездные без тренеров
        if results['no_trainers']:
            details += "═" * 80 + "\n"
            details += "👨‍🏫 ВЫЕЗДНЫЕ МЕРОПРИЯТИЯ БЕЗ ТРЕНЕРОВ\n"
            details += "═" * 80 + "\n\n"
            for issue in results['no_trainers']:
                details += f"{issue_num}. {issue['name']}\n"
                details += f"   Месяц: {issue['month']}\n"
                details += f"   Проблема: {issue['issue']}\n"
                details += f"   ID: {issue['id']}\n\n"
                issue_num += 1
        
        self.details_text.insert('1.0', details)
        self.details_text.config(state='disabled')
    
    def _save_report(self):
        """Сохранить отчёт в файл"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Сохранить отчёт проверки",
            defaultextension=".txt",
            filetypes=[
                ("Текстовый файл", "*.txt"),
                ("Все файлы", "*.*")
            ],
            initialfile=f"data_check_{self.year}.txt"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"ОТЧЁТ ПРОВЕРКИ ЦЕЛОСТНОСТИ ДАННЫХ\n")
                f.write(f"Год: {self.year}\n")
                f.write(f"=" * 80 + "\n\n")
                
                # Резюме
                summary = self.summary_text.get('1.0', tk.END)
                f.write(summary)
                f.write("\n" + "=" * 80 + "\n\n")
                
                # Детали
                details = self.details_text.get('1.0', tk.END)
                f.write(details)
            
            messagebox.showinfo("Успешно", f"Отчёт сохранён:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")

