import logging
import psutil
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Класс для сбора метрик производительности и вычисления фитнес-функции.
    Соответствует модулю metrics_collector из архитектурного плана.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация калькулятора метрик.
        
        Args:
            config: Конфигурация фитнес-функции из config.py
        """
        self.config = config
        logger.info("MetricsCalculator инициализирован")
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """
        Собирает метрики системы (CPU, I/O, память).
        
        Returns:
            Dict: Системные метрики
        """
        metrics = {}
        
        try:
            # CPU usage
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            metrics['memory_available_gb'] = memory.available / (1024**3)
            
            # Disk I/O (сбор статистики)
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics['disk_read_mb'] = disk_io.read_bytes / (1024**2)
                metrics['disk_write_mb'] = disk_io.write_bytes / (1024**2)
                metrics['disk_io_total_mb'] = (disk_io.read_bytes + disk_io.write_bytes) / (1024**2)
            
            logger.info(f"Системные метрики: CPU={metrics['cpu_percent']}%, "
                       f"Memory={metrics['memory_percent']}%")
            
        except Exception as e:
            logger.error(f"Ошибка при сборе системных метрик: {e}")
        
        return metrics
    
    def calculate_fitness(self, load_test_metrics: Dict[str, float],
                         system_metrics: Dict[str, float]) -> float:
        """
        Вычисляет значение фитнес-функции на основе собранных метрик.
        Fitness = (TP_weight * (TP/TP_target)) + 
                 (1/(latency/MAX_LATENCY)) * LATENCY_weight - 
                 CPU_weight * (CPU/100) - 
                 IO_weight * (IO/IO_max)
        
        Args:
            load_test_metrics: Метрики нагрузочного тестирования
            system_metrics: Системные метрики
            
        Returns:
            float: Значение фитнес-функции (чем выше, тем лучше)
        """
        try:
            fitness = 0.0
            penalties = 0.0
            bonuses = 0.0
            
            # Пропускная способность (чем больше, тем лучше)
            tp_target = self.config['TARGET_TP']
            tp = load_test_metrics.get('throughput', 0)
            tp_score = min(tp / tp_target, 2.0)  # ограничиваем максимум 200%
            bonuses += self.config['TP_WEIGHT'] * tp_score
            
            # Задержка (чем меньше, тем лучше)
            max_latency = self.config['MAX_LATENCY']
            latency = load_test_metrics.get('avg_latency', max_latency * 2)
            if latency <= max_latency:
                # Если задержка в норме, добавляем бонус
                latency_score = max_latency / max(latency, 1)
                bonuses += self.config['LATENCY_WEIGHT'] * latency_score
            else:
                # Если задержка превышена, накладываем штраф
                penalties += self.config['LATENCY_WEIGHT'] * (latency / max_latency - 1)
            
            # CPU usage (штраф за высокую загрузку)
            cpu = system_metrics.get('cpu_percent', 50)
            cpu_penalty = max(0, (cpu - 70) / 30) if cpu > 70 else 0
            penalties += self.config['CPU_WEIGHT'] * cpu_penalty
            
            # I/O usage (штраф за высокую нагрузку)
            io = system_metrics.get('disk_io_total_mb', 0)
            io_max = 100  # MB/s, эмпирическое значение
            io_penalty = min(io / io_max, 1.0)
            penalties += self.config['IO_WEIGHT'] * io_penalty
            
            # Дополнительный штраф за ошибки
            error_rate = load_test_metrics.get('error_rate', 0)
            penalties += error_rate * 2  # сильный штраф за ошибки
            
            # Итоговая фитнес-функция
            fitness = bonuses - penalties
            
            # Нормализация до разумного диапазона
            fitness = max(fitness, 0.0)
            fitness = min(fitness, 2.0)
            
            logger.info(f"Fitness calculation: bonuses={bonuses:.3f}, "
                       f"penalties={penalties:.3f}, fitness={fitness:.3f}")
            
            return fitness
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении фитнес-функции: {e}")
            return 0.0