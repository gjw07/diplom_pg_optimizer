#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль командной строки (CLI) для управления PG Optimizer.
Обеспечивает интерфейс для запуска оптимизации и анализа результатов.
"""

import argparse
import sys
import os
import logging
from datetime import datetime

# Настройка логирования для CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_environment():
    """
    Настройка окружения перед запуском.
    Создает необходимые директории и проверяет наличие зависимостей.
    """
    # Создаем директории для результатов
    dirs = ['./results', './logs', './plots', './configs']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Проверяем наличие Docker
    try:
        import docker
        client = docker.from_env()
        client.ping()
        logger.info("Docker доступен")
    except Exception as e:
        logger.warning(f"Docker не доступен: {e}")
        logger.warning("Убедитесь, что Docker установлен и запущен")
    
    # Проверяем наличие JMeter
    import subprocess
    try:
        result = subprocess.run(['jmeter', '--version'], 
                                capture_output=True, 
                                text=True)
        if result.returncode == 0:
            logger.info("JMeter найден")
        else:
            logger.warning("JMeter не найден в PATH")
    except FileNotFoundError:
        logger.warning("JMeter не найден в PATH")
    
    logger.info("Окружение настроено")


def run_optimization(args):
    """
    Запуск процесса оптимизации.
    """
    logger.info("=" * 60)
    logger.info("ЗАПУСК ОПТИМИЗАЦИИ")
    logger.info("=" * 60)
    
    setup_environment()
    
    try:
        # Импортируем функцию из модуля run_experiment (относительный импорт)
        from pg_optimizer.run_experiment import run_experiment
        run_experiment()
    except Exception as e:
        logger.error(f"Ошибка при выполнении оптимизации: {e}")
        sys.exit(1)


def analyze_results(args):
    """
    Анализ результатов оптимизации.
    """
    logger.info("=" * 60)
    logger.info("АНАЛИЗ РЕЗУЛЬТАТОВ")
    logger.info("=" * 60)
    
    try:
        # Импортируем функцию из модуля analyze_results (относительный импорт)
        from pg_optimizer.analyze_results import analyze
        analyze()
    except Exception as e:
        logger.error(f"Ошибка при анализе результатов: {e}")
        sys.exit(1)


def show_info(args):
    """
    Вывод информации о проекте.
    """
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    PG OPTIMIZER v1.0.0                          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Автоматическая оптимизация производительности PostgreSQL       ║
    ║  с использованием генетических алгоритмов                      ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Автор:     Табачкова А.М.                                      ║
    ║  Группа:    246                                                 ║
    ║  ВУЗ:       РГРТУ им. В.Ф. Уткина                               ║
    ║  Кафедра:   САПР                                                ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Технологии:                                                    ║
    ║    - PostgreSQL (объект оптимизации)                           ║
    ║    - Python + DEAP (генетический алгоритм)                     ║
    ║    - Docker (контейнеризация)                                  ║
    ║    - JMeter (нагрузочное тестирование)                         ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Команды:                                                       ║
    ║    pg-optimizer run      - запустить оптимизацию               ║
    ║    pg-optimizer analyze  - проанализировать результаты         ║
    ║    pg-optimizer info     - показать информацию                 ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)


def main():
    """
    Главная функция точки входа.
    """
    parser = argparse.ArgumentParser(
        prog="pg-optimizer",
        description="PG Optimizer - оптимизация производительности PostgreSQL",
        epilog="Пример использования: pg-optimizer run"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    # Команда для запуска оптимизации
    run_parser = subparsers.add_parser("run", help="Запустить оптимизацию")
    run_parser.add_argument("--config", "-c", type=str, 
                           help="Путь к файлу конфигурации (опционально)")
    
    # Команда для анализа результатов
    analyze_parser = subparsers.add_parser("analyze", help="Анализировать результаты")
    analyze_parser.add_argument("--results-dir", "-d", type=str, 
                               help="Путь к директории с результатами")
    
    # Команда для информации
    subparsers.add_parser("info", help="Показать информацию о проекте")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_optimization(args)
    elif args.command == "analyze":
        analyze_results(args)
    elif args.command == "info":
        show_info(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()