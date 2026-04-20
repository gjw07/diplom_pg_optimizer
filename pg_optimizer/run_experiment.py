"""
Точка входа для запуска экспериментов.
Реализует Этап 5 из Плана 2.
"""

import logging
import sys
from datetime import datetime

# Импортируем все модули
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
    Выполняет все этапы оптимизации согласно Плану 2.
    """
    logger.info("=" * 70)
    logger.info("ЗАПУСК ЭКСПЕРИМЕНТА ПО ОПТИМИЗАЦИИ POSTGRESQL")
    logger.info("=" * 70)
    
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
        orchestrator = OptimizationOrchestrator(
            db, load_tester, metrics, ga, config
        )
        
        # 5. Запуск базового теста
        logger.info("=" * 70)
        logger.info("Этап 5: Запуск теста с базовой конфигурацией (Baseline)")
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
        
        logger.info("=" * 70)
        logger.info("ЭКСПЕРИМЕНТ УСПЕШНО ЗАВЕРШЕН")
        logger.info(f"Результаты сохранены в: {config.PATHS['RESULTS_DIR']}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в эксперименте: {e}", exc_info=True)
        # Пытаемся остановить контейнер в случае ошибки
        try:
            db.stop_container()
        except:
            pass



   
if __name__ == "__main__":
    run_experiment()