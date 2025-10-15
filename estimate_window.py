# -*- coding: utf-8 -*-
"""
Окно для управления сметами выездных мероприятий
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from models import Event, Estimate, EstimateItem
from styles import apply_styles, COLORS, create_styled_button, FONT_FAMILY
import webbrowser
import os
import html
from datetime import datetime
import math


def round_up_to_10(value):
    """
    Округлить в большую сторону до 10
    Например: 1001 -> 1010, 1005 -> 1010, 1010 -> 1010
    """
    return math.ceil(value / 10) * 10


class EstimateWindow:
    """Класс окна управления сметами"""
    
    def __init__(self, parent, db, event: Event):
        """
        Инициализация окна смет
        
        Args:
            parent: Родительское окно
            db: Объект базы данных
            event: Мероприятие, для которого создаются сметы
        """
        self.db = db
        self.event = event
        self.estimates = []
        
        # Создаём окно
        self.window = tk.Toplevel(parent)
        self.window.title(f"Сметы - {event.name}")
        self.window.geometry("1200x800")
        self.window.transient(parent)
        
        # Применяем стили
        apply_styles(self.window)
        
        # Обработчик закрытия окна
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._create_widgets()
        self._load_estimates()
    
    def _create_widgets(self):
        """Создать виджеты окна"""
        # Заголовок
        header_frame = ttk.Frame(self.window, padding="15")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text=f"📋 Управление сметами",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            header_frame,
            text=f"{self.event.name} ({self.event.month} {self.event.year}, {self.event.location})",
            font=(FONT_FAMILY, 10)
        ).pack(side=tk.LEFT, padx=15)
        
        # Панель кнопок
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(fill=tk.X)
        
        create_styled_button(
            button_frame,
            "➕ Создать смету на ППО",
            lambda: self._create_estimate('ППО'),
            'primary'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "➕ Создать смету на тренера (УЭВП)",
            lambda: self._create_estimate('УЭВП'),
            'accent'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "✏️ Редактировать",
            self._edit_selected_estimate,
            'secondary'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "🖨️ Печать",
            self._print_selected_estimate,
            'normal'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "🗑️ Удалить",
            self._delete_selected_estimate,
            'normal'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            button_frame,
            "🔄 Обновить",
            self._load_estimates,
            'normal'
        ).pack(side=tk.LEFT, padx=5)
        
        # Список смет
        list_frame = ttk.Frame(self.window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Таблица смет
        columns = ('type', 'trainer', 'total', 'items')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('type', text='Тип сметы')
        self.tree.heading('trainer', text='Тренер/Назначение')
        self.tree.heading('total', text='Итого, руб.')
        self.tree.heading('items', text='Статей расходов')
        
        self.tree.column('type', width=150)
        self.tree.column('trainer', width=300)
        self.tree.column('total', width=150)
        self.tree.column('items', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка закрытия внизу
        close_frame = ttk.Frame(self.window, padding="10")
        close_frame.pack(fill=tk.X)
        
        create_styled_button(
            close_frame,
            "Закрыть",
            self.window.destroy,
            'normal'
        ).pack(side=tk.RIGHT, padx=5)
    
    def _load_estimates(self):
        """Загрузить список смет"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Загружаем сметы из БД
        estimates_data = self.db.get_estimates_by_event(self.event.id)
        self.estimates = [Estimate.from_db_row(row) for row in estimates_data]
        
        # Заполняем таблицу
        for estimate in self.estimates:
            # Получаем количество статей расходов
            items = self.db.get_estimate_items(estimate.id)
            items_count = len(items)
            
            # Определяем отображаемое имя
            if estimate.estimate_type == 'УЭВП' and estimate.trainer_name:
                display_name = estimate.trainer_name
            else:
                display_name = "Спортсмены (дети)"
            
            self.tree.insert('', 'end', values=(
                estimate.estimate_type,
                display_name,
                f"{estimate.total_amount:,.2f}".replace(',', ' '),
                items_count
            ), tags=(estimate.id,))
    
    def _create_estimate(self, estimate_type: str):
        """Создать новую смету"""
        # Создаём окно для выбора тренера (если УЭВП)
        dialog = EstimateEditDialog(self.window, self.db, self.event, None, estimate_type)
        if dialog.result:
            self._load_estimates()
    
    def _edit_selected_estimate(self):
        """Редактировать выбранную смету"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите смету для редактирования")
            return
        
        # Получаем ID сметы
        estimate_id = int(self.tree.item(selection[0], 'tags')[0])
        estimate = next((e for e in self.estimates if e.id == estimate_id), None)
        
        if estimate:
            dialog = EstimateEditDialog(self.window, self.db, self.event, estimate)
            if dialog.result:
                self._load_estimates()
    
    def _delete_selected_estimate(self):
        """Удалить выбранную смету"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите смету для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную смету?\nВсе статьи расходов также будут удалены."):
            estimate_id = int(self.tree.item(selection[0], 'tags')[0])
            self.db.delete_estimate(estimate_id)
            self._load_estimates()
    
    def _print_selected_estimate(self):
        """Сформировать и открыть смету для печати"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите смету для печати")
            return
        
        estimate_id = int(self.tree.item(selection[0], 'tags')[0])
        estimate = next((e for e in self.estimates if e.id == estimate_id), None)
        
        if estimate:
            self._generate_estimate_html(estimate)


    def _generate_estimate_html(self, estimate: Estimate):
        """Сгенерировать HTML документ сметы"""
        # Получаем статьи расходов
        items_data = self.db.get_estimate_items(estimate.id)
        items = [EstimateItem.from_db_row(row) for row in items_data]
        
        # Группируем по категориям
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        # Формируем HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Смета - {estimate.estimate_type}</title>
    <style>
        @page {{ size: A4; margin: 10mm; }}
        body {{
            font-family: 'Times New Roman', Times, serif;
            font-size: 14px;
            margin: 0;
            padding: 20px;
        }}
        .center {{
            text-align: center;
            font-weight: bold;
            margin: 30px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .total {{
            font-weight: bold;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="center">
        СМЕТА<br>
        командировочных расходов {'тренера' if estimate.estimate_type == 'УЭВП' else ''} для сопровождения спортсменов ДЮСК "Ямбург",<br>
        {html.escape(self.event.name)}
    </div>
    
    <p><strong>Место проведения:</strong> {html.escape(estimate.place or self.event.location)}</p>
    <p><strong>Сроки проведения:</strong> {html.escape(estimate.start_date or '')} - {html.escape(estimate.end_date or '')}</p>
"""
        
        # Добавляем тренера для смет УЭВП
        if estimate.estimate_type == 'УЭВП' and estimate.trainer_name:
            html_content += f"    <p><strong>тренер:</strong> {html.escape(estimate.trainer_name)}</p>\n"
        
        # Таблица расходов
        html_content += """
    <table>
        <thead>
            <tr>
                <th>№</th>
                <th>Наименование расходов</th>
                <th>Кол-во чел.</th>
                <th>Дни/Стороны</th>
                <th>Ставка, руб.</th>
                <th>Сумма, руб.</th>
            </tr>
        </thead>
        <tbody>
"""
        
        item_number = 1
        category_order = ['Проезд', 'Проживание', 'Суточные', 'Питание']
        
        for category in category_order:
            if category in categories:
                # Заголовок категории с трёхзначной нумерацией (например: 1.001)
                formatted_number = f"1.{item_number:03d}"
                html_content += f"""
            <tr>
                <td><strong>{formatted_number}</strong></td>
                <td colspan="5"><strong>{category}</strong></td>
            </tr>
"""
                
                for item in categories[category]:
                    desc = html.escape(item.description) if item.description else ""
                    html_content += f"""
            <tr>
                <td></td>
                <td>{desc}</td>
                <td style="text-align: center;">{item.people_count}</td>
                <td style="text-align: center;">{item.days_count}</td>
                <td style="text-align: right;">{item.rate:,.2f}</td>
                <td style="text-align: right;">{item.total:,.2f}</td>
            </tr>
"""
                item_number += 1
        
        # Итого
        html_content += f"""
            <tr class="total">
                <td colspan="5">ИТОГО по смете:</td>
                <td style="text-align: right;">{estimate.total_amount:,.2f}</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
"""
        
        # Сохраняем и открываем
        filename = f"smeta_{estimate.estimate_type}_{estimate.id}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Открываем в браузере
        webbrowser.open('file://' + os.path.realpath(filename))
        messagebox.showinfo("Успешно", f"Смета сформирована и открыта в браузере:\n{filename}")


class EstimateEditDialog:
    """Диалог создания/редактирования сметы"""
    
    def __init__(self, parent, db, event: Event, estimate: Estimate = None, estimate_type: str = None):
        """
        Args:
            parent: Родительское окно
            db: Объект базы данных
            event: Мероприятие
            estimate: Смета для редактирования (None для создания)
            estimate_type: Тип сметы ('ППО' или 'УЭВП') для создания
        """
        self.db = db
        self.event = event
        self.estimate = estimate
        self.estimate_type = estimate_type if estimate_type else (estimate.estimate_type if estimate else 'ППО')
        self.result = False
        
        # Создаём диалоговое окно
        self.window = tk.Toplevel(parent)
        self.window.title("Редактирование сметы" if estimate else "Создание сметы")
        self.window.geometry("900x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        apply_styles(self.window)
        
        self._create_widgets()
        
        if estimate:
            self._load_estimate_data()
        
        self.window.wait_window()
    
    def _create_widgets(self):
        """Создать виджеты диалога"""
        # Информация о мероприятии
        info_frame = ttk.Frame(self.window, padding="10")
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text=f"Мероприятие: {self.event.name}", font=(FONT_FAMILY, 11, 'bold')).pack(anchor='w')
        ttk.Label(info_frame, text=f"Место: {self.event.location}", font=(FONT_FAMILY, 9)).pack(anchor='w')
        
        # Отображение заложенной суммы
        budget_frame = tk.Frame(self.window, bg='#FFF3CD', relief='solid', bd=1, padx=10, pady=8)
        budget_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Определяем заложенную сумму в зависимости от типа сметы
        if self.estimate_type == 'ППО':
            planned_budget = self.event.children_budget
            budget_label = "Заложенная сумма на детей (ППО)"
        else:  # УЭВП
            # Для УЭВП - это сумма на одного тренера
            if self.event.trainers_count > 0:
                planned_budget = self.event.trainers_budget / self.event.trainers_count
            else:
                planned_budget = self.event.trainers_budget
            budget_label = "Заложенная сумма на тренера (УЭВП)"
        
        self.planned_budget = planned_budget
        
        ttk.Label(
            budget_frame,
            text=f"💰 {budget_label}: {planned_budget:,.2f} руб.".replace(',', ' '),
            font=(FONT_FAMILY, 10, 'bold'),
            background='#FFF3CD'
        ).pack(side=tk.LEFT)
        
        # Основные данные сметы
        main_frame = ttk.LabelFrame(self.window, text=f"Смета {self.estimate_type}", padding="10")
        main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Тренер (только для УЭВП)
        if self.estimate_type == 'УЭВП':
            ttk.Label(main_frame, text="ФИО тренера:").grid(row=0, column=0, sticky='w', pady=5)
            self.trainer_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=self.trainer_var, width=50).grid(row=0, column=1, pady=5, sticky='ew')
        
        # Место и даты
        ttk.Label(main_frame, text="Место проведения:").grid(row=1, column=0, sticky='w', pady=5)
        self.place_var = tk.StringVar(value=self.event.location)
        ttk.Entry(main_frame, textvariable=self.place_var, width=50).grid(row=1, column=1, pady=5, sticky='ew')
        
        ttk.Label(main_frame, text="Дата начала:").grid(row=2, column=0, sticky='w', pady=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.start_date_var, width=20).grid(row=2, column=1, pady=5, sticky='w')
        
        ttk.Label(main_frame, text="Дата окончания:").grid(row=3, column=0, sticky='w', pady=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.end_date_var, width=20).grid(row=3, column=1, pady=5, sticky='w')
        
        main_frame.columnconfigure(1, weight=1)
        
        # Статьи расходов
        items_frame = ttk.LabelFrame(self.window, text="Статьи расходов", padding="10")
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Кнопки добавления статей
        btn_frame = ttk.Frame(items_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="➕ Проезд", command=lambda: self._add_item('Проезд')).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➕ Проживание", command=lambda: self._add_item('Проживание')).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➕ Суточные", command=lambda: self._add_item('Суточные')).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➕ Питание", command=lambda: self._add_item('Питание')).pack(side=tk.LEFT, padx=2)
        
        # Таблица статей
        columns = ('category', 'description', 'people', 'days', 'rate', 'total')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings', height=10)
        
        self.items_tree.heading('category', text='Категория')
        self.items_tree.heading('description', text='Описание/Маршрут')
        self.items_tree.heading('people', text='Чел.')
        self.items_tree.heading('days', text='Дни')
        self.items_tree.heading('rate', text='Ставка')
        self.items_tree.heading('total', text='Сумма')
        
        self.items_tree.column('category', width=100)
        self.items_tree.column('description', width=250)
        self.items_tree.column('people', width=60)
        self.items_tree.column('days', width=60)
        self.items_tree.column('rate', width=100)
        self.items_tree.column('total', width=100)
        
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Двойной клик для редактирования
        self.items_tree.bind('<Double-1>', lambda e: self._edit_item())
        
        # Кнопки действий над статьями
        items_btn_frame = ttk.Frame(items_frame)
        items_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(items_btn_frame, text="✏️ Редактировать", command=self._edit_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(items_btn_frame, text="🗑️ Удалить", command=self._delete_item).pack(side=tk.LEFT, padx=2)
        
        # Итого с индикацией превышения бюджета
        total_frame = tk.Frame(self.window, bg='#E8F5E9', relief='solid', bd=1, padx=10, pady=10)
        total_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.total_label = tk.Label(
            total_frame, 
            text="ИТОГО: 0.00 руб.", 
            font=(FONT_FAMILY, 12, 'bold'),
            bg='#E8F5E9'
        )
        self.total_label.pack(side=tk.LEFT)
        
        self.budget_status_label = tk.Label(
            total_frame,
            text="",
            font=(FONT_FAMILY, 10),
            bg='#E8F5E9'
        )
        self.budget_status_label.pack(side=tk.LEFT, padx=20)
        
        # Кнопки сохранения/отмены
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(fill=tk.X)
        
        create_styled_button(button_frame, "💾 Сохранить", self._save, 'primary').pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, "Отмена", self.window.destroy, 'normal').pack(side=tk.LEFT, padx=5)
    
    def _load_estimate_data(self):
        """Загрузить данные сметы для редактирования"""
        if self.estimate_type == 'УЭВП' and self.estimate.trainer_name:
            self.trainer_var.set(self.estimate.trainer_name)
        
        self.place_var.set(self.estimate.place or '')
        self.start_date_var.set(self.estimate.start_date or '')
        self.end_date_var.set(self.estimate.end_date or '')
        
        # Загружаем статьи расходов
        items_data = self.db.get_estimate_items(self.estimate.id)
        for item_data in items_data:
            item = EstimateItem.from_db_row(item_data)
            self.items_tree.insert('', 'end', values=(
                item.category,
                item.description,
                item.people_count,
                item.days_count,
                f"{item.rate:.2f}",
                f"{item.total:.2f}"
            ), tags=(item.id,))
        
        self._update_total()
    
    def _add_item(self, category: str):
        """Добавить статью расходов"""
        dialog = EstimateItemDialog(self.window, category)
        if dialog.result:
            self.items_tree.insert('', 'end', values=(
                dialog.category,
                dialog.description,
                dialog.people_count,
                dialog.days_count,
                f"{dialog.rate:.2f}",
                f"{dialog.total:.2f}"
            ), tags=(None,))  # None означает новая статья
            self._update_total()
    
    def _edit_item(self):
        """Редактировать статью расходов"""
        selection = self.items_tree.selection()
        if not selection:
            return
        
        item = self.items_tree.item(selection[0])
        values = item['values']
        
        dialog = EstimateItemDialog(
            self.window,
            category=values[0],
            description=values[1],
            people_count=int(values[2]),
            days_count=int(values[3]),
            rate=float(values[4])
        )
        
        if dialog.result:
            self.items_tree.item(selection[0], values=(
                dialog.category,
                dialog.description,
                dialog.people_count,
                dialog.days_count,
                f"{dialog.rate:.2f}",
                f"{dialog.total:.2f}"
            ))
            self._update_total()
    
    def _delete_item(self):
        """Удалить статью расходов"""
        selection = self.items_tree.selection()
        if selection:
            self.items_tree.delete(selection[0])
            self._update_total()
    
    def _update_total(self):
        """Обновить итоговую сумму с индикацией превышения бюджета"""
        total = 0.0
        for item in self.items_tree.get_children():
            values = self.items_tree.item(item, 'values')
            total += float(values[5])
        
        self.total_label.config(text=f"ИТОГО: {total:,.2f} руб.".replace(',', ' '))
        
        # Сравниваем с заложенным бюджетом
        difference = self.planned_budget - total
        
        if abs(difference) < 0.01:  # Практически совпадает
            status_text = "✅ Точно по плану!"
            text_color = '#2E7D32'  # Темно-зеленый
        elif difference > 0:  # Остались деньги
            status_text = f"✅ Остаток: {difference:,.2f} руб.".replace(',', ' ')
            text_color = '#2E7D32'  # Темно-зеленый
        else:  # Превышение
            status_text = f"⚠️ ПРЕВЫШЕНИЕ: {abs(difference):,.2f} руб.".replace(',', ' ')
            text_color = '#D32F2F'  # Красный
        
        self.budget_status_label.config(text=status_text, fg=text_color)
    
    def _save(self):
        """Сохранить смету"""
        # Проверяем обязательные поля
        if self.estimate_type == 'УЭВП' and not self.trainer_var.get().strip():
            messagebox.showerror("Ошибка", "Укажите ФИО тренера для сметы УЭВП")
            return
        
        # Создаём или обновляем смету
        if self.estimate:
            # Обновление
            trainer_name = self.trainer_var.get() if self.estimate_type == 'УЭВП' else None
            self.db.update_estimate(
                self.estimate.id,
                trainer_name=trainer_name,
                place=self.place_var.get(),
                start_date=self.start_date_var.get(),
                end_date=self.end_date_var.get()
            )
            estimate_id = self.estimate.id
            
            # Удаляем старые статьи
            old_items = self.db.get_estimate_items(estimate_id)
            for old_item in old_items:
                self.db.delete_estimate_item(old_item[0])
        else:
            # Создание
            trainer_name = self.trainer_var.get() if self.estimate_type == 'УЭВП' else None
            estimate_id = self.db.create_estimate(
                self.event.id,
                self.estimate_type,
                trainer_name=trainer_name,
                place=self.place_var.get(),
                start_date=self.start_date_var.get(),
                end_date=self.end_date_var.get()
            )
        
        # Добавляем статьи расходов
        total_estimate = 0.0
        for item in self.items_tree.get_children():
            values = self.items_tree.item(item, 'values')
            self.db.add_estimate_item(
                estimate_id,
                category=values[0],
                description=values[1],
                people_count=int(values[2]),
                days_count=int(values[3]),
                rate=float(values[4])
            )
            # Суммируем итоговую сумму сметы
            total_estimate += float(values[5])
        
        # ОБНОВЛЯЕМ БЮДЖЕТ МЕРОПРИЯТИЯ на основе сметы
        if self.estimate_type == 'ППО':
            # Обновляем бюджет на детей
            cursor = self.db.connection.cursor()
            cursor.execute("""
                UPDATE events 
                SET children_budget = ? 
                WHERE id = ?
            """, (total_estimate, self.event.id))
            self.db.connection.commit()
        elif self.estimate_type == 'УЭВП':
            # Для УЭВП нужно пересчитать общий бюджет на тренеров
            # Получаем все сметы УЭВП для этого мероприятия
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT e.id FROM estimates e
                WHERE e.event_id = ? AND e.estimate_type = 'УЭВП'
            """, (self.event.id,))
            uevp_estimates = cursor.fetchall()
            
            # Суммируем все сметы УЭВП
            total_trainers_budget = 0.0
            for est_row in uevp_estimates:
                est_id = est_row[0]
                items = self.db.get_estimate_items(est_id)
                # Структура кортежа: (id, estimate_id, category, description, people_count, days_count, rate, total)
                total_trainers_budget += sum(item[7] for item in items)  # total в индексе 7
            
            # Обновляем общий бюджет на тренеров
            cursor.execute("""
                UPDATE events 
                SET trainers_budget = ? 
                WHERE id = ?
            """, (total_trainers_budget, self.event.id))
            self.db.connection.commit()
        
        self.result = True
        self.window.destroy()


class EstimateItemDialog:
    """Диалог добавления/редактирования статьи расходов"""
    
    def __init__(self, parent, category: str = "", description: str = "",
                 people_count: int = 0, days_count: int = 0, rate: float = 0.0):
        self.result = False
        self.category = category
        self.description = description
        self.people_count = people_count
        self.days_count = days_count
        self.rate = rate
        self.total = 0.0
        
        # Создаём диалоговое окно
        self.window = tk.Toplevel(parent)
        self.window.title(f"Статья расходов - {category}")
        self.window.geometry("500x350")
        self.window.transient(parent)
        self.window.grab_set()
        
        apply_styles(self.window)
        
        self._create_widgets()
        self._calculate_total()
        
        self.window.wait_window()
    
    def _create_widgets(self):
        """Создать виджеты диалога"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Категория
        ttk.Label(main_frame, text="Категория:", font=(FONT_FAMILY, 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        ttk.Label(main_frame, text=self.category, font=(FONT_FAMILY, 10)).grid(row=0, column=1, sticky='w', pady=5)
        
        # Описание/маршрут
        ttk.Label(main_frame, text="Описание/Маршрут:").grid(row=1, column=0, sticky='w', pady=5)
        self.desc_var = tk.StringVar(value=self.description)
        ttk.Entry(main_frame, textvariable=self.desc_var, width=40).grid(row=1, column=1, sticky='ew', pady=5)
        
        # Количество человек
        ttk.Label(main_frame, text="Количество человек:").grid(row=2, column=0, sticky='w', pady=5)
        self.people_var = tk.IntVar(value=self.people_count)
        people_spin = ttk.Spinbox(main_frame, from_=0, to=100, textvariable=self.people_var, width=10)
        people_spin.grid(row=2, column=1, sticky='w', pady=5)
        people_spin.bind('<KeyRelease>', lambda e: self._calculate_total())
        
        # Количество дней
        ttk.Label(main_frame, text="Количество дней/сторон:").grid(row=3, column=0, sticky='w', pady=5)
        self.days_var = tk.IntVar(value=self.days_count)
        days_spin = ttk.Spinbox(main_frame, from_=0, to=100, textvariable=self.days_var, width=10)
        days_spin.grid(row=3, column=1, sticky='w', pady=5)
        days_spin.bind('<KeyRelease>', lambda e: self._calculate_total())
        
        # Ставка
        ttk.Label(main_frame, text="Ставка, руб.:").grid(row=4, column=0, sticky='w', pady=5)
        self.rate_var = tk.DoubleVar(value=self.rate)
        rate_entry = ttk.Entry(main_frame, textvariable=self.rate_var, width=15)
        rate_entry.grid(row=4, column=1, sticky='w', pady=5)
        rate_entry.bind('<KeyRelease>', lambda e: self._calculate_total())
        
        # Сумма
        ttk.Label(main_frame, text="Итого:").grid(row=5, column=0, sticky='w', pady=5)
        self.total_label = ttk.Label(main_frame, text="0.00 руб.", font=(FONT_FAMILY, 11, 'bold'))
        self.total_label.grid(row=5, column=1, sticky='w', pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        # Кнопки
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(fill=tk.X)
        
        create_styled_button(button_frame, "Сохранить", self._save, 'primary').pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, "Отмена", self.window.destroy, 'normal').pack(side=tk.LEFT, padx=5)
    
    def _calculate_total(self):
        """Рассчитать итоговую сумму (ставка округляется в большую сторону до 10)"""
        try:
            people = self.people_var.get()
            days = self.days_var.get()
            rate_raw = self.rate_var.get()
            # Округляем ставку в большую сторону до 10
            rate_rounded = round_up_to_10(rate_raw)
            # Обновляем отображение ставки, если она изменилась
            if rate_rounded != rate_raw:
                self.rate_var.set(rate_rounded)
            # Итоговая сумма = люди * дни * округленная ставка
            self.total = people * days * rate_rounded
            self.total_label.config(text=f"{self.total:,.2f} руб.".replace(',', ' '))
        except:
            pass
    
    def _save(self):
        """Сохранить статью"""
        self.description = self.desc_var.get()
        self.people_count = self.people_var.get()
        self.days_count = self.days_var.get()
        self.rate = self.rate_var.get()
        self.result = True
        self.window.destroy()

