#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import time
import logging
import json
import random
from typing import Dict, Any, Tuple
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed

from pg_optimizer.test_queries import TestQueries

logger = logging.getLogger(__name__)


class LoadTester:
    """
    Класс для проведения нагрузочного тестирования.
    Автоматически определяет схему БД и использует соответствующие запросы.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация нагрузочного тестера.
        
        Args:
            config: Конфигурация JMeter из config.py
        """
        self.config = config
        self.use_jmeter = self._check_jmeter()
        self.schema_level = None  # Будет определено при первом тесте
        self.queries_module = None  # Будет загружен при определении схемы
        
        if self.use_jmeter:
            logger.info("LoadTester инициализирован с использованием JMeter")
        else:
            logger.info("LoadTester инициализирован с использованием встроенного генератора")
    
    def _check_jmeter(self) -> bool:
        """Проверяет, доступен ли JMeter."""
        jmeter_path = self.config.get('JMETER_PATH', 'jmeter')
        if not os.path.exists(jmeter_path):
            return False
        return True
    
    def _detect_schema(self) -> str:
        """
        Определяет, какая схема БД используется.
        Проверяет наличие характерных таблиц.
        
        Returns:
            str: 'simple', 'medium' или 'complex'
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Проверяем наличие таблиц для разных схем
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            logger.info(f"Обнаружены таблицы: {tables}")
            
            # Определяем схему по наличию таблиц
            if 'projects' in tables and 'employee_projects' in tables:
                if 'skills' in tables or 'locations' in tables:
                    logger.info("Определена схема: COMPLEX")
                    return 'complex'
                else:
                    logger.info("Определена схема: MEDIUM")
                    return 'medium'
            elif 'departments' in tables and 'employees' in tables:
                logger.info("Определена схема: SIMPLE")
                return 'simple'
            else:
                logger.warning("Не удалось определить схему, используем MEDIUM по умолчанию")
                return 'medium'
                
        except Exception as e:
            logger.warning(f"Ошибка определения схемы: {e}, используем MEDIUM")
            return 'medium'
    
    def _load_queries_for_schema(self, schema_level: str):
        """
        Загружает запросы для соответствующей схемы.
        
        Args:
            schema_level: 'simple', 'medium' или 'complex'
        """
        if schema_level == 'simple':
            from .schemas import simple_schema
            self.queries_module = simple_schema
        elif schema_level == 'complex':
            from .schemas import complex_schema
            self.queries_module = complex_schema
        else:
            from .schemas import medium_schema
            self.queries_module = medium_schema
        
        logger.info(f"Загружены запросы для схемы: {schema_level.upper()}")
    
    def _get_query(self, query_type: str = 'mixed') -> str:
        """
        Возвращает случайный запрос для текущей схемы.
        
        Args:
            query_type: 'simple', 'medium', 'complex', 'very_complex', 'mixed'
        
        Returns:
            str: SQL-запрос
        """
        if self.queries_module is None:
            # Определяем схему и загружаем запросы
            self.schema_level = self._detect_schema()
            self._load_queries_for_schema(self.schema_level)
        
        queries = self.queries_module.get_test_queries()
        
        if query_type == 'simple':
            return random.choice(queries.get('simple', ["SELECT 1"]))
        elif query_type == 'medium':
            return random.choice(queries.get('medium', ["SELECT 1"]))
        elif query_type == 'complex':
            return random.choice(queries.get('complex', ["SELECT 1"]))
        elif query_type == 'very_complex':
            return random.choice(queries.get('very_complex', queries.get('complex', ["SELECT 1"])))
        else:  # mixed
            weights = [0.3, 0.4, 0.2, 0.1]
            types = ['simple', 'medium', 'complex', 'very_complex']
            chosen_type = random.choices(types, weights=weights)[0]
            return self._get_query(chosen_type)
    
    def _get_db_connection(self):
        """Создаёт соединение с PostgreSQL"""
        return psycopg2.connect(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_password",
            database="test_db"
        )
    
    def _execute_query(self, conn, query: str) -> Tuple[float, bool, int]:
        """Выполняет один запрос и измеряет время."""
        try:
            start = time.perf_counter()
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
            elapsed_ms = (time.perf_counter() - start) * 1000
            return elapsed_ms, True, len(rows)
        except Exception as e:
            logger.debug(f"Ошибка запроса: {e}")
            return 0, False, 0
    
    def _run_single_workload(self, duration_seconds: int, 
                            query_weights: Dict[str, float]) -> Dict[str, Any]:
        """Запускает один поток нагрузки."""
        conn = self._get_db_connection()
        end_time = time.time() + duration_seconds
        
        results = {
            'total_queries': 0,
            'successful': 0,
            'total_time_ms': 0,
            'min_time_ms': float('inf'),
            'max_time_ms': 0,
            'by_type': {}
        }
        
        try:
            while time.time() < end_time:
                # Выбираем тип запроса согласно весам
                query_type = random.choices(
                    list(query_weights.keys()),
                    weights=list(query_weights.values())
                )[0]
                
                # Получаем запрос для текущей схемы
                query = self._get_query(query_type)
                
                elapsed_ms, success, _ = self._execute_query(conn, query)
                
                if success:
                    results['successful'] += 1
                    results['total_time_ms'] += elapsed_ms
                    results['min_time_ms'] = min(results['min_time_ms'], elapsed_ms)
                    results['max_time_ms'] = max(results['max_time_ms'], elapsed_ms)
                    
                    if query_type not in results['by_type']:
                        results['by_type'][query_type] = {'count': 0, 'total_time_ms': 0}
                    results['by_type'][query_type]['count'] += 1
                    results['by_type'][query_type]['total_time_ms'] += elapsed_ms
                
                results['total_queries'] += 1
                time.sleep(random.uniform(0.01, 0.05))
                
        finally:
            conn.close()
        
        return results
    
    def _run_parallel_workload(self, duration_seconds: int, num_threads: int,
                               query_weights: Dict[str, float]) -> Dict[str, Any]:
        """Запускает параллельную нагрузку в несколько потоков."""
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self._run_single_workload, duration_seconds, query_weights)
                for _ in range(num_threads)
            ]
            
            all_results = []
            for future in as_completed(futures):
                all_results.append(future.result())
        
        # Агрегация результатов
        aggregated = {
            'total_queries': 0,
            'successful': 0,
            'total_time_ms': 0,
            'min_time_ms': float('inf'),
            'max_time_ms': 0,
            'tps': 0,
            'avg_latency_ms': 0,
            'by_type': {}
        }
        
        for r in all_results:
            aggregated['total_queries'] += r['total_queries']
            aggregated['successful'] += r['successful']
            aggregated['total_time_ms'] += r['total_time_ms']
            aggregated['min_time_ms'] = min(aggregated['min_time_ms'], r['min_time_ms'])
            aggregated['max_time_ms'] = max(aggregated['max_time_ms'], r['max_time_ms'])
            
            for qtype, stats in r['by_type'].items():
                if qtype not in aggregated['by_type']:
                    aggregated['by_type'][qtype] = {'count': 0, 'total_time_ms': 0}
                aggregated['by_type'][qtype]['count'] += stats['count']
                aggregated['by_type'][qtype]['total_time_ms'] += stats['total_time_ms']
        
        if aggregated['successful'] > 0:
            aggregated['tps'] = aggregated['successful'] / duration_seconds
            aggregated['avg_latency_ms'] = aggregated['total_time_ms'] / aggregated['successful']
        
        for qtype in aggregated['by_type']:
            count = aggregated['by_type'][qtype]['count']
            if count > 0:
                aggregated['by_type'][qtype]['avg_latency_ms'] = \
                    aggregated['by_type'][qtype]['total_time_ms'] / count
                aggregated['by_type'][qtype]['tps'] = count / duration_seconds
        
        return aggregated
    
    def run_test(self, test_name: str = "test") -> str:
        """
        Запускает нагрузочный тест.
        
        Returns:
            str: Путь к файлу с результатами (JSON)
        """
        results_dir = self.config.get('RESULTS_DIR', './results/')
        os.makedirs(results_dir, exist_ok=True)
        
        test_duration = self.config.get('TEST_DURATION', 30)
        num_threads = self.config.get('WORKLOAD_PARALLEL', 4)
        query_mix = self.config.get('WORKLOAD_QUERY_MIX', 'mixed')
        
        # Настройка весов запросов
        if query_mix == 'oltp':
            query_weights = {'simple': 0.7, 'medium': 0.2, 'complex': 0.07, 'very_complex': 0.03}
        elif query_mix == 'olap':
            query_weights = {'simple': 0.1, 'medium': 0.2, 'complex': 0.4, 'very_complex': 0.3}
        else:  # mixed
            query_weights = {'simple': 0.3, 'medium': 0.4, 'complex': 0.2, 'very_complex': 0.1}
        
        logger.info(f"Запуск нагрузочного теста: {test_name}")
        logger.info(f"  Длительность: {test_duration} сек, Потоков: {num_threads}")
        logger.info(f"  Тип нагрузки: {query_mix}")
        
        # Запускаем нагрузку
        results = self._run_parallel_workload(test_duration, num_threads, query_weights)
        
        # Формируем результат
        metrics = {
            'throughput': results.get('tps', 0),
            'avg_latency': results.get('avg_latency_ms', 0),
            'min_latency': results.get('min_time_ms', 0),
            'max_latency': results.get('max_time_ms', 0),
            'error_rate': 1 - (results.get('successful', 0) / max(results.get('total_queries', 1), 1)),
            'total_requests': results.get('total_queries', 0),
            'successful_requests': results.get('successful', 0),
            'queries_by_type': results.get('by_type', {})
        }
        
        # Сохраняем результаты
        results_file = os.path.join(results_dir, f"{test_name}_workload.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Результаты сохранены в: {results_file}")
        logger.info(f"  Throughput: {metrics['throughput']:.2f} TPS")
        logger.info(f"  Avg Latency: {metrics['avg_latency']:.2f} ms")
        logger.info(f"  Error Rate: {metrics['error_rate']*100:.2f}%")
        
        if metrics.get('queries_by_type'):
            logger.info("  Статистика по типам запросов:")
            for qtype, stats in metrics['queries_by_type'].items():
                logger.info(f"    {qtype}: {stats['count']} запр., "
                           f"TPS={stats.get('tps', 0):.2f}, "
                           f"Latency={stats.get('avg_latency_ms', 0):.2f} ms")
        
        return results_file
    
    def parse_results(self, results_file: str) -> Dict[str, float]:
        """Парсит результаты нагрузочного тестирования."""
        metrics = {
            'throughput': 0.0,
            'avg_latency': 0.0,
            'min_latency': 0.0,
            'max_latency': 0.0,
            'error_rate': 0.0,
            'total_requests': 0,
            'successful_requests': 0
        }
        
        try:
            if not os.path.exists(results_file):
                logger.error(f"Файл результатов не найден: {results_file}")
                return metrics
            
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metrics.update(data)
            
            logger.info(f"Загружены результаты: Throughput={metrics['throughput']:.2f} TPS")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге результатов: {e}")
        
        return metrics