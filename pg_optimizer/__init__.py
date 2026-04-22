#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PG Optimizer - Автоматическая оптимизация производительности PostgreSQL
с использованием генетических алгоритмов

Выпускная квалификационная работа
Студент: Табачкова А.М.
Группа: 246
Тема: Оптимизация производительности клиент-серверных приложений баз данных
      с использованием генетических алгоритмов

Данный пакет реализует:
- Модуль управления PostgreSQL в Docker-контейнере
- Модуль нагрузочного тестирования на основе Apache JMeter
- Модуль сбора метрик и расчета фитнес-функции
- Модуль гибридного генетического алгоритма
- Модуль оркестрации процесса оптимизации
- Модули визуализации и анализа результатов
"""

__version__ = "1.0.0"
__author__ = "Табачкова А.М."
__email__ = "student@rgrtu.ru"
__license__ = "MIT"

# Экспортируем основные классы и функции для удобного импорта
from pg_optimizer.config import (
    OPTIMIZABLE_PARAMS,
    GA_CONFIG,
    DOCKER_CONFIG,
    JMETER_CONFIG,
    FITNESS_CONFIG,
    PATHS
)

from pg_optimizer.db_controller import DBController
from pg_optimizer.load_tester import LoadTester
from pg_optimizer.metrics_calculator import MetricsCalculator
from pg_optimizer.ga_engine import GeneticAlgorithmEngine
from pg_optimizer.orchestrator import OptimizationOrchestrator

__all__ = [
    # Конфигурация
    "OPTIMIZABLE_PARAMS",
    "GA_CONFIG",
    "DOCKER_CONFIG",
    "JMETER_CONFIG",
    "FITNESS_CONFIG",
    "PATHS",
    # Модули
    "DBController",
    "LoadTester",
    "MetricsCalculator",
    "GeneticAlgorithmEngine",
    "OptimizationOrchestrator",
]

