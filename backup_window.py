# -*- coding: utf-8 -*-
"""
Окно управления резервными копиями
"""

import tkinter as tk
from tkinter import ttk, messagebox
from backup_manager import BackupManager
from styles import apply_styles, COLORS, create_styled_button


class BackupWindow:
    """Класс окна управления резервными копиями"""
    
    def __init__(self, parent, db_path: str = "calendar_plans.db"):
        """
        Инициализация окна
        
        Args:
            parent: Родительское окно
            db_path: Путь к файлу БД
        """
        self.parent = parent
        self.backup_manager = BackupManager(db_path)
        
        # Создаём окно
        self.window = tk.Toplevel(parent)
        self.window.title("ДЮСК Ямбург - Резервное копирование")
        self.window.geometry("800x550")
        
        # Применяем единые стили
        apply_styles(self.window)
        
        # Центрируем окно
        self.window.transient(parent)
        self.window.grab_set()
        
        # Обработчик закрытия окна (для Red OS и других систем)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._create_widgets()
        self._load_backups()
    
    def _create_widgets(self):
        """Создать виджеты окна"""
        # Заголовок
        header = ttk.Label(
            self.window, 
            text="💾 Управление резервными копиями",
            style='Header.TLabel'
        )
        header.pack(pady=15)
        
        # Панель кнопок действий - в едином стиле
        action_frame = ttk.Frame(self.window)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        create_styled_button(
            action_frame, "➕ Создать резервную копию", 
            self._create_backup, style='primary'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            action_frame, "♻️ Восстановить", 
            self._restore_backup, style='secondary'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            action_frame, "🗑️ Удалить", 
            self._delete_backup, style='normal'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            action_frame, "🧹 Очистить старые", 
            self._cleanup_old, style='normal'
        ).pack(side=tk.LEFT, padx=5)
        
        create_styled_button(
            action_frame, "🔄 Обновить", 
            self._load_backups, style='normal'
        ).pack(side=tk.LEFT, padx=5)
        
        # Статистика
        self.stats_label = ttk.Label(
            self.window, 
            text="",
            font=('Arial', 9)
        )
        self.stats_label.pack(pady=5)
        
        # Таблица с бэкапами
        table_frame = ttk.Frame(self.window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("date", "size"),
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        scrollbar.config(command=self.tree.yview)
        
        # Настройка колонок
        self.tree.heading("date", text="Дата создания")
        self.tree.heading("size", text="Размер")
        
        self.tree.column("date", width=300, anchor=tk.W)
        self.tree.column("size", width=150, anchor=tk.E)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Двойной клик для восстановления
        self.tree.bind("<Double-Button-1>", lambda e: self._restore_backup())
        
        # Подсказка
        hint_label = ttk.Label(
            self.window,
            text="💡 Совет: Создавайте резервные копии перед важными изменениями. Двойной клик для восстановления.",
            font=('Arial', 9),
            foreground="gray"
        )
        hint_label.pack(pady=5)
        
        # Кнопка закрытия
        create_styled_button(
            self.window, "Закрыть", 
            self.window.destroy, style='normal'
        ).pack(pady=10)
    
    def _load_backups(self):
        """Загрузить список резервных копий"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Загружаем бэкапы
        backups = self.backup_manager.get_backups()
        
        for filename, date_str, size in backups:
            # Форматируем размер
            if size < 1024:
                size_str = f"{size} байт"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} КБ"
            else:
                size_str = f"{size / (1024 * 1024):.1f} МБ"
            
            # Добавляем в таблицу
            self.tree.insert("", tk.END, values=(date_str, size_str), tags=(filename,))
        
        # Обновляем статистику
        stats = self.backup_manager.get_backup_stats()
        stats_text = f"Всего резервных копий: {stats['count']} | "
        stats_text += f"Общий размер: {stats['total_size_mb']} МБ"
        
        if stats['newest']:
            stats_text += f" | Последняя: {stats['newest']}"
        
        self.stats_label.config(text=stats_text)
    
    def _create_backup(self):
        """Создать резервную копию"""
        success, message = self.backup_manager.create_backup()
        
        if success:
            messagebox.showinfo(
                "Успех", 
                f"Резервная копия создана успешно!\n\nФайл: {message}"
            )
            self._load_backups()
        else:
            messagebox.showerror("Ошибка", message)
    
    def _restore_backup(self):
        """Восстановить из резервной копии"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("Внимание", "Выберите резервную копию для восстановления")
            return
        
        # Получаем имя файла из tags
        item = selection[0]
        filename = self.tree.item(item, "tags")[0]
        date_str = self.tree.item(item, "values")[0]
        
        # Подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Восстановить базу данных из резервной копии от {date_str}?\n\n"
            "⚠ ВНИМАНИЕ: Текущие данные будут заменены!\n"
            "Текущая БД будет сохранена как резервная копия перед восстановлением."
        )
        
        if not confirm:
            return
        
        success, message = self.backup_manager.restore_backup(filename)
        
        if success:
            messagebox.showinfo("Успех", f"{message}\n\nПерезапустите программу для применения изменений.")
            self.window.destroy()
        else:
            messagebox.showerror("Ошибка", message)
    
    def _delete_backup(self):
        """Удалить резервную копию"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("Внимание", "Выберите резервную копию для удаления")
            return
        
        # Получаем имя файла из tags
        item = selection[0]
        filename = self.tree.item(item, "tags")[0]
        date_str = self.tree.item(item, "values")[0]
        
        # Подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Удалить резервную копию от {date_str}?"
        )
        
        if not confirm:
            return
        
        success, message = self.backup_manager.delete_backup(filename)
        
        if success:
            messagebox.showinfo("Успех", message)
            self._load_backups()
        else:
            messagebox.showerror("Ошибка", message)
    
    def _cleanup_old(self):
        """Очистить старые резервные копии"""
        stats = self.backup_manager.get_backup_stats()
        
        if stats['count'] <= 10:
            messagebox.showinfo(
                "Информация",
                f"Найдено {stats['count']} резервных копий.\n\n"
                "Очистка не требуется (сохраняются последние 10)."
            )
            return
        
        to_delete = stats['count'] - 10
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Будет удалено {to_delete} старых резервных копий.\n"
            f"Останется последних 10.\n\nПродолжить?"
        )
        
        if not confirm:
            return
        
        deleted = self.backup_manager.cleanup_old_backups(keep_count=10)
        
        messagebox.showinfo("Успех", f"Удалено резервных копий: {deleted}")
        self._load_backups()

