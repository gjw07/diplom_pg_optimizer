#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска графического вьювера результатов
Использование: python launch_viewer.py
"""

try:
    # Запуск как часть пакета: `python -m pg_optimizer.launch_viewer`
    from results_viewer import launch_viewer
except Exception:
    # Запуск как скрипт из директории `pg_optimizer`: `python launch_viewer.py`
    from results_viewer import launch_viewer

if __name__ == "__main__":
    print("Запуск графического вьювера результатов PG Optimizer...")
    launch_viewer()