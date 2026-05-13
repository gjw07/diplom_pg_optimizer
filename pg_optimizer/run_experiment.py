#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from datetime import datetime

# Импортируем все модули из текущего пакета
from . import config
from .db_controller import DBController
from .load_tester import LoadTester
from .metrics_calculator import MetricsCalculator
from .ga_engine import GeneticAlgorithmEngine
from .orchestrator import OptimizationOrchestrator

# Настройка подробного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_experiment():
    """
    Главная функция запуска эксперимента.
    """
    logger.info("=" * 70)
    logger.info("ЗАПУСК ЭКСПЕРИМЕНТА ПО ОПТИМИЗАЦИИ POSTGRESQL")
    logger.info("=" * 70)
    
    # Получаем выбранную схему БД
    schema_level = config.DATABASE_SCHEMA.get('LEVEL', 'medium')
    logger.info(f"Выбрана схема базы данных: {schema_level.upper()}")
    logger.info(f"Описание: {config.DATABASE_SCHEMA['SCHEMAS'][schema_level]['description']}")
    
    try:
        # 1. Инициализация компонентов
        logger.info("Этап 1: Инициализация компонентов системы")
        db = DBController(config.DOCKER_CONFIG)
        load_tester = LoadTester(config.JMETER_CONFIG)
        metrics = MetricsCalculator(config.FITNESS_CONFIG)
        
        # 2. Запуск базового контейнера
        logger.info("Этап 2: Запуск тестового стенда")
        if not db.start_container():
            logger.error("Не удалось запустить контейнер с PostgreSQL")
            return
        
        # 2.5. Генерация тестовых данных (с выбранной схемой)
        logger.info(f"Этап 2.5: Генерация тестовых данных (схема: {schema_level})")
        from .generate_test_data import TestDataGenerator

        # Используем DOCKER_CONFIG напрямую
        data_generator = TestDataGenerator(config.DOCKER_CONFIG, schema_level=schema_level)
        if data_generator.connect():
            logger.info("Пересоздание тестовых данных...")
            data_generator.drop_all_tables()
            data_generator.create_all_tables()
            
            # Получаем параметры генерации из конфигурации
            # schema_level уже в нижнем регистре ('simple', 'medium', 'complex')
            schema_params = config.DATABASE_SCHEMA['SCHEMAS'][schema_level]
            counts = {
                'employees': schema_params.get('employees', 100),
                'customers': schema_params.get('customers', 200),
                'products': schema_params.get('products', 50),
                'orders': schema_params.get('orders', 500)
            }
            
            data_generator.generate_full_dataset(counts)
            data_generator.disconnect()
        else:
            logger.warning("Не удалось подключиться для генерации данных")
        
        # 3. Инициализация GA Engine
        logger.info("Этап 3: Инициализация генетического алгоритма")
        
        # Временно создаем заглушку для функции оценки
        def dummy_evaluate(individual):
            return (0.5,)
        
        ga = GeneticAlgorithmEngine(
            config.OPTIMIZABLE_PARAMS,
            config.GA_CONFIG,
            dummy_evaluate
        )
        
        # 4. Создание оркестратора
        logger.info("Этап 4: Создание оркестратора")
        orchestrator = OptimizationOrchestrator(db, load_tester, metrics, ga)
        
        # 5. Запуск базового теста
        logger.info("=" * 70)
        logger.info("Этап 5: Запуск теста с базовой конфигурацией")
        baseline_results = orchestrator.run_baseline_test()
        
        # 6. Запуск оптимизации
        logger.info("=" * 70)
        logger.info("Этап 6: Запуск процесса оптимизации")
        optimization_results = orchestrator.run_optimization()
        
        # 7. Валидация лучшей конфигурации
        logger.info("=" * 70)
        logger.info("Этап 7: Валидация лучшей найденной конфигурации")
        validation_results = orchestrator.validate_best_config(
            optimization_results['best_config']
        )
        
        # 8. Сравнение результатов
        logger.info("=" * 70)
        logger.info("Этап 8: Сравнение результатов")
        
        baseline_tp = baseline_results['load_metrics'].get('throughput', 0)
        best_tp = validation_results['load_metrics'].get('throughput', 0)
        improvement = ((best_tp - baseline_tp) / baseline_tp * 100) if baseline_tp > 0 else 0
        
        logger.info(f"Базовая конфигурация (Throughput): {baseline_tp:.2f} TPS")
        logger.info(f"Оптимизированная конфигурация (Throughput): {best_tp:.2f} TPS")
        logger.info(f"Улучшение: {improvement:.1f}%")
        
        # 9. Очистка
        logger.info("=" * 70)
        logger.info("Этап 9: Очистка ресурсов")
        orchestrator.cleanup()

        logger.info("Сохранение отчетов...")
        report_file = orchestrator.save_all_reports(
            baseline_results,
            optimization_results,
            validation_results
        )
        
        logger.info(f"Полный отчет сохранен в: {report_file}")
        logger.info(f"Все результаты доступны в папке: {config.PATHS['RESULTS_DIR']}logs/")

        logger.info("Запуск графического вьювера результатов...")
        try:
            from pg_optimizer.results_viewer import launch_viewer
            launch_viewer()
        except Exception as e:
            logger.error(f"Не удалось запустить вьювер: {e}")
        
        logger.info("=" * 70)
        logger.info("ЭКСПЕРИМЕНТ УСПЕШНО ЗАВЕРШЕН")
        logger.info(f"Результаты сохранены в: {config.PATHS['RESULTS_DIR']}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в эксперименте: {e}", exc_info=True)


if __name__ == "__main__":
    run_experiment()