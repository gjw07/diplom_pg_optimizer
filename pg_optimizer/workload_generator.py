#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор рабочей нагрузки для нагрузочного тестирования.
Использует сложные запросы из test_queries.py.
"""

import random
import time
import logging
import psycopg2
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from pg_optimizer.test_queries import TestQueries

logger = logging.getLogger(__name__)


class WorkloadGenerator:
    """
    Генератор смешанной рабочей нагрузки для PostgreSQL.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Инициализация генератора нагрузки.
        
        Args:
            db_config: Конфигурация подключения к БД
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
        # Веса для разных типов запросов при смешанной нагрузке
        self.query_weights = {
            'simple': 0.30,      # 30% простых запросов
            'medium': 0.40,      # 40% средних запросов
            'complex': 0.20,     # 20% сложных запросов
            'very_complex': 0.10 # 10% очень сложных запросов
        }
        
    def connect(self) -> bool:
        """Устанавливает соединение с PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                port=self.db_config['PORT'],
                user=self.db_config['POSTGRES_USER'],
                password=self.db_config['POSTGRES_PASSWORD'],
                database=self.db_config['POSTGRES_DB']
            )
            self.cursor = self.conn.cursor()
            logger.info("WorkloadGenerator: соединение с PostgreSQL установлено")
            return True
        except Exception as e:
            logger.error(f"WorkloadGenerator: ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Закрывает соединение"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("WorkloadGenerator: соединение закрыто")
    
    def execute_query(self, query: str, query_type: str = 'unknown') -> Tuple[float, bool, int]:
        """
        Выполняет один запрос и измеряет время выполнения.
        
        Returns:
            Tuple[float, bool, int]: (время выполнения в мс, успех/ошибка, количество строк)
        """
        try:
            start_time = time.perf_counter()
            self.cursor.execute(query)
            # Получаем все результаты, чтобы запрос реально выполнился
            rows = self.cursor.fetchall()
            end_time = time.perf_counter()
            
            elapsed_ms = (end_time - start_time) * 1000
            row_count = len(rows)
            
            logger.debug(f"Запрос [{query_type}] выполнен: {elapsed_ms:.2f} ms, строк: {row_count}")
            return elapsed_ms, True, row_count
            
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса [{query_type}]: {e}")
            return 0.0, False, 0
    
    def run_single_workload(self, duration_seconds: int = 30) -> Dict[str, Any]:
        """
        Запускает один сеанс нагрузочного тестирования.
        
        Args:
            duration_seconds: Длительность теста в секундах
            
        Returns:
            Dict: Результаты тестирования
        """
        end_time = time.time() + duration_seconds
        
        results = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_time_ms': 0,
            'min_time_ms': float('inf'),
            'max_time_ms': 0,
            'queries_by_type': {
                'simple': {'count': 0, 'total_time_ms': 0},
                'medium': {'count': 0, 'total_time_ms': 0},
                'complex': {'count': 0, 'total_time_ms': 0},
                'very_complex': {'count': 0, 'total_time_ms': 0}
            }
        }
        
        logger.info(f"Запуск нагрузочного теста на {duration_seconds} секунд...")
        
        while time.time() < end_time:
            # Выбираем тип запроса согласно весам
            query_type = random.choices(
                list(self.query_weights.keys()),
                weights=list(self.query_weights.values())
            )[0]
            
            # Получаем запрос соответствующего типа
            if query_type == 'simple':
                query = TestQueries.get_random_simple_query()
            elif query_type == 'medium':
                query = TestQueries.get_random_medium_query()
            elif query_type == 'complex':
                query = TestQueries.get_random_complex_query()
            else:
                query = TestQueries.get_random_very_complex_query()
            
            # Выполняем запрос
            elapsed_ms, success, row_count = self.execute_query(query, query_type)
            
            if success:
                results['successful_queries'] += 1
                results['total_time_ms'] += elapsed_ms
                results['min_time_ms'] = min(results['min_time_ms'], elapsed_ms)
                results['max_time_ms'] = max(results['max_time_ms'], elapsed_ms)
                
                results['queries_by_type'][query_type]['count'] += 1
                results['queries_by_type'][query_type]['total_time_ms'] += elapsed_ms
            else:
                results['failed_queries'] += 1
            
            results['total_queries'] += 1
            
            # Небольшая задержка между запросами для имитации реальной нагрузки
            time.sleep(random.uniform(0.01, 0.1))
        
        # Обработка результатов
        if results['successful_queries'] > 0:
            results['avg_time_ms'] = results['total_time_ms'] / results['successful_queries']
        else:
            results['avg_time_ms'] = 0
        
        if results['min_time_ms'] == float('inf'):
            results['min_time_ms'] = 0
        
        # Расчет TPS (транзакций в секунду)
        results['tps'] = results['successful_queries'] / duration_seconds
        
        # Расчет TPS по типам запросов
        for qtype in results['queries_by_type']:
            count = results['queries_by_type'][qtype]['count']
            results['queries_by_type'][qtype]['tps'] = count / duration_seconds
            if count > 0:
                results['queries_by_type'][qtype]['avg_time_ms'] = \
                    results['queries_by_type'][qtype]['total_time_ms'] / count
            else:
                results['queries_by_type'][qtype]['avg_time_ms'] = 0
        
        return results
    
    def run_parallel_workload(self, duration_seconds: int = 30, 
                              num_threads: int = 4) -> Dict[str, Any]:
        """
        Запускает параллельную нагрузку (несколько потоков).
        
        Args:
            duration_seconds: Длительность теста
            num_threads: Количество потоков
            
        Returns:
            Dict: Агрегированные результаты
        """
        logger.info(f"Запуск параллельной нагрузки: {num_threads} потоков, {duration_seconds} сек")
        
        # Запускаем потоки
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self.run_single_workload, duration_seconds)
                for _ in range(num_threads)
            ]
            
            results_list = []
            for future in as_completed(futures):
                try:
                    results_list.append(future.result())
                except Exception as e:
                    logger.error(f"Ошибка в потоке: {e}")
        
        # Агрегация результатов
        aggregated = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_time_ms': 0,
            'min_time_ms': float('inf'),
            'max_time_ms': 0,
            'tps': 0,
            'queries_by_type': {
                'simple': {'count': 0, 'total_time_ms': 0, 'tps': 0, 'avg_time_ms': 0},
                'medium': {'count': 0, 'total_time_ms': 0, 'tps': 0, 'avg_time_ms': 0},
                'complex': {'count': 0, 'total_time_ms': 0, 'tps': 0, 'avg_time_ms': 0},
                'very_complex': {'count': 0, 'total_time_ms': 0, 'tps': 0, 'avg_time_ms': 0}
            }
        }
        
        for r in results_list:
            aggregated['total_queries'] += r['total_queries']
            aggregated['successful_queries'] += r['successful_queries']
            aggregated['failed_queries'] += r['failed_queries']
            aggregated['tps'] += r['tps']
            aggregated['min_time_ms'] = min(aggregated['min_time_ms'], r['min_time_ms'])
            aggregated['max_time_ms'] = max(aggregated['max_time_ms'], r['max_time_ms'])
            
            for qtype in aggregated['queries_by_type']:
                aggregated['queries_by_type'][qtype]['count'] += r['queries_by_type'][qtype]['count']
                aggregated['queries_by_type'][qtype]['total_time_ms'] += r['queries_by_type'][qtype]['total_time_ms']
        
        # Пересчет средних
        if aggregated['successful_queries'] > 0:
            aggregated['avg_time_ms'] = sum(r['avg_time_ms'] * r['successful_queries'] 
                                           for r in results_list) / aggregated['successful_queries']
        
        for qtype in aggregated['queries_by_type']:
            count = aggregated['queries_by_type'][qtype]['count']
            if count > 0:
                aggregated['queries_by_type'][qtype]['avg_time_ms'] = \
                    aggregated['queries_by_type'][qtype]['total_time_ms'] / count
        
        # Сохраняем метрики для фитнес-функции
        aggregated['throughput'] = aggregated['tps']
        aggregated['avg_latency'] = aggregated['avg_time_ms']
        
        return aggregated


def run_load_test(db_config: Dict[str, Any], duration: int = 30, 
                  parallel: int = 1) -> Dict[str, Any]:
    """
    Упрощенная функция запуска нагрузочного теста.
    
    Args:
        db_config: Конфигурация БД
        duration: Длительность в секундах
        parallel: Количество параллельных потоков
    
    Returns:
        Dict: Результаты теста
    """
    generator = WorkloadGenerator(db_config)
    
    if not generator.connect():
        return {
            'throughput': 0,
            'avg_latency': 0,
            'min_latency': 0,
            'max_latency': 0,
            'error_rate': 0,
            'total_queries': 0,
            'successful_queries': 0
        }
    
    if parallel > 1:
        results = generator.run_parallel_workload(duration, parallel)
    else:
        results = generator.run_single_workload(duration)
    
    generator.disconnect()
    
    return {
        'throughput': results.get('tps', 0),
        'avg_latency': results.get('avg_time_ms', 0),
        'min_latency': results.get('min_time_ms', 0),
        'max_latency': results.get('max_time_ms', 0),
        'error_rate': results.get('failed_queries', 0) / max(results.get('total_queries', 1), 1),
        'total_queries': results.get('total_queries', 0),
        'successful_queries': results.get('successful_queries', 0),
        'queries_by_type': results.get('queries_by_type', {})
    }


if __name__ == "__main__":
    # Тестирование генератора нагрузки
    logging.basicConfig(level=logging.INFO)
    
    from pg_optimizer import config
    
    generator = WorkloadGenerator(config.DOCKER_CONFIG)
    
    if generator.connect():
        print("\n" + "=" * 60)
        print("Тестирование генератора нагрузки")
        print("=" * 60)
        
        # Однопоточный тест
        results = generator.run_single_workload(10)
        print(f"\nРезультаты (один поток):")
        print(f"  TPS: {results['tps']:.2f}")
        print(f"  Средняя задержка: {results['avg_time_ms']:.2f} ms")
        print(f"  Успешных запросов: {results['successful_queries']}")
        
        # Вывод статистики по типам запросов
        print("\nСтатистика по типам запросов:")
        for qtype, stats in results['queries_by_type'].items():
            print(f"  {qtype}: {stats['count']} запросов, TPS={stats['tps']:.2f}, "
                  f"среднее={stats['avg_time_ms']:.2f} ms")
        
        generator.disconnect()