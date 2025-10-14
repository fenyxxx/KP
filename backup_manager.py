# -*- coding: utf-8 -*-
"""
Менеджер резервного копирования базы данных
"""

import os
import shutil
from datetime import datetime
from typing import List, Tuple


class BackupManager:
    """Класс для управления резервными копиями БД"""
    
    def __init__(self, db_path: str = "calendar_plans.db", backup_dir: str = "backups"):
        """
        Инициализация менеджера резервных копий
        
        Args:
            db_path: Путь к файлу базы данных
            backup_dir: Директория для хранения резервных копий
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Создаём директорию для бэкапов если её нет
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self) -> Tuple[bool, str]:
        """
        Создать резервную копию БД
        
        Returns:
            Tuple[bool, str]: (успех, сообщение/путь к бэкапу)
        """
        try:
            if not os.path.exists(self.db_path):
                return False, "Файл базы данных не найден"
            
            # Формируем имя файла бэкапа с датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"calendar_plans_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Копируем файл БД
            shutil.copy2(self.db_path, backup_path)
            
            return True, backup_path
        
        except Exception as e:
            return False, f"Ошибка при создании резервной копии: {str(e)}"
    
    def get_backups(self) -> List[Tuple[str, str, int]]:
        """
        Получить список доступных резервных копий
        
        Returns:
            List[Tuple[str, str, int]]: Список кортежей (имя файла, дата, размер в байтах)
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("calendar_plans_backup_") and filename.endswith(".db"):
                    filepath = os.path.join(self.backup_dir, filename)
                    
                    # Получаем время модификации файла
                    mtime = os.path.getmtime(filepath)
                    date_str = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M:%S")
                    
                    # Получаем размер файла
                    size = os.path.getsize(filepath)
                    
                    backups.append((filename, date_str, size))
            
            # Сортируем по дате (новые первыми)
            backups.sort(key=lambda x: x[0], reverse=True)
            
        except Exception as e:
            print(f"Ошибка при получении списка бэкапов: {e}")
        
        return backups
    
    def restore_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """
        Восстановить базу данных из резервной копии
        
        Args:
            backup_filename: Имя файла резервной копии
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return False, "Файл резервной копии не найден"
            
            # Создаём бэкап текущей БД перед восстановлением
            if os.path.exists(self.db_path):
                current_backup = f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                current_backup_path = os.path.join(self.backup_dir, current_backup)
                shutil.copy2(self.db_path, current_backup_path)
            
            # Восстанавливаем из бэкапа
            shutil.copy2(backup_path, self.db_path)
            
            return True, "База данных успешно восстановлена"
        
        except Exception as e:
            return False, f"Ошибка при восстановлении: {str(e)}"
    
    def delete_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """
        Удалить резервную копию
        
        Args:
            backup_filename: Имя файла резервной копии
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return False, "Файл резервной копии не найден"
            
            os.remove(backup_path)
            return True, "Резервная копия удалена"
        
        except Exception as e:
            return False, f"Ошибка при удалении: {str(e)}"
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Удалить старые резервные копии, оставив указанное количество новых
        
        Args:
            keep_count: Количество последних бэкапов для сохранения
        
        Returns:
            int: Количество удалённых бэкапов
        """
        backups = self.get_backups()
        deleted_count = 0
        
        # Если бэкапов больше чем нужно оставить
        if len(backups) > keep_count:
            # Удаляем старые (они в конце списка после сортировки)
            for backup in backups[keep_count:]:
                filename = backup[0]
                success, _ = self.delete_backup(filename)
                if success:
                    deleted_count += 1
        
        return deleted_count
    
    def get_backup_stats(self) -> dict:
        """
        Получить статистику по резервным копиям
        
        Returns:
            dict: Словарь со статистикой
        """
        backups = self.get_backups()
        
        total_size = sum(backup[2] for backup in backups)
        
        return {
            'count': len(backups),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'newest': backups[0][1] if backups else None,
            'oldest': backups[-1][1] if backups else None
        }

