#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для просмотра сохраненных результатов
"""

import os
from pathlib import Path
import webbrowser


def view_latest_report():
    """Открывает последний сгенерированный отчет"""
    results_dir = Path("../experiment_results/logs")
    
    if not results_dir.exists():
        print("Результаты не найдены. Сначала запустите оптимизацию.")
        return
    
    # Находим последний MD файл
    md_files = list(results_dir.glob("report_*.md"))
    if not md_files:
        print("Markdown отчеты не найдены")
        return
    
    latest_report = max(md_files, key=os.path.getctime)
    
    print(f"Открываю отчет: {latest_report}")
    
    # Пытаемся открыть в браузере для лучшего отображения
    try:
        webbrowser.open(str(latest_report.absolute()))
        print("Отчет открыт в браузере")
    except:
        # Если не получилось, выводим в консоль
        with open(latest_report, 'r', encoding='utf-8') as f:
            print("\n" + "="*80)
            print(f.read())
            print("="*80)


def list_all_reports():
    """Показывает список всех сохраненных отчетов"""
    results_dir = Path("./experiment_results/logs")
    
    if not results_dir.exists():
        print("Результаты не найдены")
        return
    
    print("\nСохраненные отчеты:\n")
    
    reports = list(results_dir.glob("report_*.md"))
    for report in sorted(reports, reverse=True):
        size = report.stat().st_size
        print(f"  - {report.name} ({size} bytes)")
    
    print(f"\nПолный путь: {results_dir.absolute()}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_all_reports()
    else:
        view_latest_report()