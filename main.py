# -*- coding: utf-8 -*-
"""
Точка входа в приложение Календарные планы
"""

import tkinter as tk
from main_window import MainWindow


def main():
    """Главная функция запуска приложения"""
    root = tk.Tk()
    app = MainWindow(root)
    app.run()


if __name__ == "__main__":
    main()

