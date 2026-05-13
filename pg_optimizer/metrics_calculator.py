#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import psutil
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Класс для сбора метрик производительности и вычисления фитнес-функции.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация калькулятора метрик.
        
        Args:
            config: Конфигурация фитнес-функции из config.py
        """
        self.config = config
        self.baseline_throughput = None
        self.baseline_latency = None
        logger.info("MetricsCalculator инициализирован")
    
    def set_baseline(self, throughput: float, latency: float):
        """Устанавливает базовые показатели (из baseline теста)"""
        self.baseline_throughput = throughput
        self.baseline_latency = latency
        logger.info(f"Baseline установлен: TPS={throughput:.2f}, Latency={latency:.2f}ms")
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """Собирает метрики системы (CPU, I/O, память)."""
        metrics = {}
        
        try:
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            metrics['memory_available_gb'] = memory.available / (1024**3)
            
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics['disk_io_total_mb'] = (disk_io.read_bytes + disk_io.write_bytes) / (1024**2)
            
            logger.info(f"Системные метрики: CPU={metrics['cpu_percent']}%, Memory={metrics['memory_percent']}%")
            
        except Exception as e:
            logger.error(f"Ошибка при сборе системных метрик: {e}")
        
        return metrics
    
    def calculate_fitness(self, load_test_metrics: Dict[str, float],
                        system_metrics: Dict[str, float]) -> float:
        tp = load_test_metrics.get('throughput', 0)
        latency = load_test_metrics.get('avg_latency', 100)
        error_rate = load_test_metrics.get('error_rate', 0)
        cpu = system_metrics.get('cpu_percent', 50)
        
        if error_rate > 0.05:
            return 0.0
        
        # Если есть baseline — используем относительную оценку
        if self.baseline_throughput is not None and self.baseline_throughput > 0:
            tp_score = tp / self.baseline_throughput
            latency_score = self.baseline_latency / max(latency, 0.1)
        else:
            tp_target = self.config.get('TARGET_TP', 150)
            tp_score = tp / tp_target
            latency_score = self.config.get('MAX_LATENCY', 100) / max(latency, 0.1)
        
        # Ограничиваем
        tp_score = min(tp_score, 2.0)
        latency_score = min(latency_score, 2.0)
        
        cpu_penalty = cpu / 100.0
        
        fitness = (tp_score * 0.6) + (latency_score * 0.3) - (cpu_penalty * 0.1)
        
        # НЕ ОГРАНИЧИВАЕМ максимум, чтобы алгоритм видел улучшения
        fitness = max(fitness, 0.0)  # только минимум
        
        logger.info(f"Fitness: tp={tp:.2f}({tp_score:.3f}), lat={latency:.2f}({latency_score:.3f}), "
                    f"cpu={cpu:.1f}% -> fitness={fitness:.3f}")
        
        return fitness