#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any
import logging

# Относительный импорт
from . import config
from .logger_config import get_logger, ExperimentLogger

logger = logging.getLogger(__name__)


class OptimizationOrchestrator:
    """
    Класс-оркестратор, управляющий всем процессом оптимизации.
    """
    
    def __init__(self, db_controller, load_tester, metrics_calculator, ga_engine):
        """
        Инициализация оркестратора.
        
        Args:
            db_controller: Контроллер БД
            load_tester: Нагрузочный тестер
            metrics_calculator: Калькулятор метрик
            ga_engine: Движок генетического алгоритма
        """
        self.db = db_controller
        self.load_tester = load_tester
        self.metrics = metrics_calculator
        self.ga = ga_engine
        
        # Создаем директории для результатов
        os.makedirs(config.PATHS['RESULTS_DIR'], exist_ok=True)
        os.makedirs(config.PATHS['LOGS_DIR'], exist_ok=True)
        os.makedirs(config.PATHS['CONFIGS_DIR'], exist_ok=True)
        
        # Инициализируем CSV файл для записи результатов
        self.results_file = self._init_results_file()
        self.exp_logger = get_logger()
        self.exp_logger.log("Инициализация оркестратора оптимизации")
        
        logger.info("OptimizationOrchestrator инициализирован")
    
    def _init_results_file(self) -> str:
        """Инициализирует CSV файл для записи результатов экспериментов."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.PATHS['RESULTS_DIR']}optimization_{timestamp}.csv"
        
        # Заголовки колонок
        headers = ['generation', 'individual', 'fitness', 'throughput', 
                   'avg_latency', 'error_rate', 'cpu_usage', 'memory_usage']
        
        # Добавляем заголовки для каждого параметра
        for param_name in config.OPTIMIZABLE_PARAMS.keys():
            headers.append(param_name)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        
        logger.info(f"Файл результатов создан: {filename}")
        return filename
    
    def evaluate_individual(self, individual: list) -> tuple:
        """Оценивает одну особь (конфигурацию) на реальной системе."""
        self.exp_logger.log(f"Начало оценки особи...")
        # Преобразуем индивидуум в конфигурацию
        indiv_config = self.ga.individual_to_config(individual)
        
        logger.info(f"Оценка конфигурации: {indiv_config}")
        
        try:
            # Применяем конфигурацию
            if not self.db.apply_config(indiv_config):
                logger.error("Не удалось применить конфигурацию")
                return (0.0,)
            
            # Перезапускаем БД
            if not self.db.restart_db():
                logger.error("Не удалось перезапустить БД")
                return (0.0,)
            
            # Запускаем нагрузочный тест
            test_name = f"gen_{len(self.ga.generation_stats)}"
            results_file = self.load_tester.run_test(test_name)
            
            if not results_file:
                logger.error("Не удалось запустить нагрузочный тест")
                return (0.0,)
            
            # Парсим результаты теста
            load_metrics = self.load_tester.parse_results(results_file)
            
            # Собираем системные метрики
            system_metrics = self.metrics.collect_system_metrics()
            
            # Вычисляем фитнес
            fitness = self.metrics.calculate_fitness(load_metrics, system_metrics)
            
            # Сохраняем результаты в CSV
            self._save_results(len(self.ga.generation_stats), individual, fitness,
                              load_metrics, system_metrics, indiv_config)
            
            logger.info(f"Фитнес для конфигурации: {fitness:.3f}")
            self.exp_logger.log_evaluation(
            len(self.ga.generation_stats), 
            0,  # individual_id можно добавить
            fitness, 
            load_metrics, 
            indiv_config
            )
        
            return (fitness,)
            
        except Exception as e:
            logger.error(f"Ошибка при оценке особи: {e}")
            return (0.0,)
    
    def _save_results(self, generation: int, individual: list, fitness: float,
                     load_metrics: Dict, system_metrics: Dict, indiv_config: Dict):
        """Сохраняет результаты оценки в CSV файл."""
        row = [
            generation,
            '_'.join(map(str, individual)),
            f"{fitness:.4f}",
            f"{load_metrics.get('throughput', 0):.2f}",
            f"{load_metrics.get('avg_latency', 0):.2f}",
            f"{load_metrics.get('error_rate', 0):.4f}",
            f"{system_metrics.get('cpu_percent', 0):.2f}",
            f"{system_metrics.get('memory_percent', 0):.2f}"
        ]
        
        # Добавляем значения параметров
        for param_name in config.OPTIMIZABLE_PARAMS.keys():
            row.append(str(indiv_config.get(param_name, '')))
        
        with open(self.results_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def run_baseline_test(self) -> Dict:
        """Запускает тест с базовой (стандартной) конфигурацией."""
        logger.info("Запуск теста с базовой конфигурацией")
        
        # Используем стандартную конфигурацию PostgreSQL
        baseline_config = {
            'shared_buffers': 128,
            'work_mem': 4,
            'maintenance_work_mem': 64,
            'random_page_cost': 4.0,
            'effective_cache_size': 512,
            'checkpoint_timeout': 300
        }
        
        # Применяем конфигурацию
        self.db.apply_config(baseline_config)
        self.db.restart_db()
        
        # Запускаем тест
        results_file = self.load_tester.run_test("baseline")
        load_metrics = self.load_tester.parse_results(results_file)
        system_metrics = self.metrics.collect_system_metrics()
        
        baseline_results = {
            'config': baseline_config,
            'load_metrics': load_metrics,
            'system_metrics': system_metrics
        }
        
        # Сохраняем результаты
        with open(f"{config.PATHS['RESULTS_DIR']}baseline.json", 'w', encoding='utf-8') as f:
            json.dump(baseline_results, f, indent=2)
        
        logger.info(f"Базовая конфигурация: Throughput={load_metrics.get('throughput', 0):.2f} TPS")
        
        return baseline_results
    
    def run_optimization(self) -> Dict:
        """Запускает полный процесс оптимизации."""
        logger.info("=" * 60)
        logger.info("ЗАПУСК ПРОЦЕССА ОПТИМИЗАЦИИ")
        logger.info("=" * 60)
        
        # Переопределяем функцию оценки в GA engine
        self.ga.toolbox.register("evaluate", self.evaluate_individual)
        
        # Запускаем оптимизацию
        best_individual, logbook = self.ga.run_optimization()
        
        # Получаем лучшую конфигурацию
        best_config = self.ga.individual_to_config(best_individual)
        best_fitness = best_individual.fitness.values[0]
        
        logger.info("=" * 60)
        logger.info("ОПТИМИЗАЦИЯ ЗАВЕРШЕНА")
        logger.info(f"Лучшая конфигурация: {best_config}")
        logger.info(f"Лучший фитнес: {best_fitness}")
        logger.info("=" * 60)
        
        # Сохраняем результаты
        results = {
            'best_config': best_config,
            'best_fitness': best_fitness,
            'generation_stats': self.ga.generation_stats,
            'logbook': str(logbook)
        }
        
        with open(f"{config.PATHS['RESULTS_DIR']}optimization_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def validate_best_config(self, best_config: Dict) -> Dict:
        """Проводит валидационный тест лучшей найденной конфигурации."""
        logger.info("Запуск валидационного теста лучшей конфигурации")
        
        # Применяем конфигурацию
        self.db.apply_config(best_config)
        self.db.restart_db()
        
        # Запускаем тест
        results_file = self.load_tester.run_test("validation")
        load_metrics = self.load_tester.parse_results(results_file)
        system_metrics = self.metrics.collect_system_metrics()
        
        validation_results = {
            'config': best_config,
            'load_metrics': load_metrics,
            'system_metrics': system_metrics
        }
        
        with open(f"{config.PATHS['RESULTS_DIR']}validation.json", 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"Валидация завершена. Throughput={load_metrics.get('throughput', 0):.2f} TPS")
        
        return validation_results
    
    def cleanup(self):
        """Очищает ресурсы (останавливает контейнер)."""
        logger.info("Очистка ресурсов")
        self.db.stop_container()

    def save_all_reports(self, baseline_results, optimization_results, validation_results):
        """Сохраняет все отчеты по окончании эксперимента"""
        
        # Сохраняем CSV лог
        self.exp_logger.save_csv_log()
        
        # Сохраняем Markdown отчет
        report_file = self.exp_logger.save_markdown_report(
            baseline_results,
            optimization_results,
            validation_results,
            self.ga.generation_stats
        )
        
        # Сохраняем JSON сводку
        summary = {
            'session_id': self.exp_logger.session_id,
            'baseline': baseline_results,
            'best_config': optimization_results.get('best_config'),
            'best_fitness': optimization_results.get('best_fitness'),
            'validation': validation_results,
            'generations': len(self.ga.generation_stats),
            'total_evaluations': len(self.ga.generation_stats) * self.ga.ga_config['POPULATION_SIZE']
        }
        self.exp_logger.save_json_summary(summary)
        
        return report_file