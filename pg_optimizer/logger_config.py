#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для форматированного логирования результатов оптимизации
"""

import logging
import json
import csv
from datetime import datetime
from typing import Dict, List, Any
import os
from pathlib import Path


class TableFormatter:
    """Класс для форматирования данных в таблицы"""
    
    @staticmethod
    def dict_to_table(data: Dict, title: str = None) -> str:
        """Преобразует словарь в Markdown таблицу"""
        lines = []
        
        if title:
            lines.append(f"\n### {title}\n")
        
        # Заголовки
        lines.append("| Параметр | Значение |")
        lines.append("|----------|----------|")
        
        # Строки данных
        for key, value in data.items():
            # Форматируем значение для читаемости
            if isinstance(value, float):
                value = f"{value:.2f}"
            lines.append(f"| {key} | {value} |")
        
        return "\n".join(lines)
    
    @staticmethod
    def list_to_table(data: List[Dict], title: str = None) -> str:
        """Преобразует список словарей в Markdown таблицу"""
        if not data:
            return ""
        
        lines = []
        if title:
            lines.append(f"\n### {title}\n")
        
        # Получаем все ключи из первого элемента
        headers = list(data[0].keys())
        
        # Заголовки
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Строки данных
        for row in data:
            formatted_row = []
            for header in headers:
                value = row.get(header, "")
                if isinstance(value, float):
                    value = f"{value:.2f}"
                formatted_row.append(str(value))
            lines.append("| " + " | ".join(formatted_row) + " |")
        
        return "\n".join(lines)
    
    @staticmethod
    def comparison_table(baseline: Dict, optimized: Dict, metrics: List[str]) -> str:
        """Создает таблицу сравнения базовой и оптимизированной конфигурации"""
        lines = ["\n### Сравнение производительности\n"]
        lines.append("| Метрика | Базовая конфигурация | Оптимизированная | Улучшение |")
        lines.append("|---------|----------------------|------------------|-----------|")
        
        for metric in metrics:
            base_val = baseline.get(metric, 0)
            opt_val = optimized.get(metric, 0)
            
            if base_val > 0:
                improvement = ((opt_val - base_val) / base_val) * 100
                improvement_str = f"{improvement:+.1f}%"
            else:
                improvement_str = "N/A"
            
            # Форматируем числа
            if isinstance(base_val, float):
                base_val = f"{base_val:.2f}"
            if isinstance(opt_val, float):
                opt_val = f"{opt_val:.2f}"
            
            lines.append(f"| {metric} | {base_val} | {opt_val} | {improvement_str} |")
        
        return "\n".join(lines)


class ExperimentLogger:
    """
    Класс для сохранения результатов экспериментов в форматированном виде
    """
    
    def __init__(self, results_dir: str = "./experiment_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем поддиректорию для логов
        self.logs_dir = self.results_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Генерируем уникальное имя для сессии
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log = []
        self.formatter = TableFormatter()
        
    def log(self, message: str, level: str = "INFO"):
        """Добавляет сообщение в лог сессии"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.session_log.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def log_config(self, title: str, config: Dict):
        """Логирует конфигурацию"""
        self.log(f"\n{title}:")
        for key, value in config.items():
            self.log(f"  {key}: {value}")
    
    def log_evaluation(self, generation: int, individual_id: int, 
                      fitness: float, metrics: Dict, config: Dict):
        """Логирует результаты оценки отдельной конфигурации"""
        self.log(f"\n--- Поколение {generation}, Особь {individual_id} ---")
        self.log(f"Фитнес: {fitness:.4f}")
        self.log("Метрики производительности:")
        self.log(f"  Throughput: {metrics.get('throughput', 0):.2f} TPS")
        self.log(f"  Avg Latency: {metrics.get('avg_latency', 0):.2f} ms")
        self.log(f"  Error Rate: {metrics.get('error_rate', 0)*100:.2f}%")
        self.log("Параметры:")
        for param, value in config.items():
            self.log(f"  {param}: {value}")
    
    def save_markdown_report(self, baseline_results: Dict, 
                            optimization_results: Dict,
                            validation_results: Dict,
                            generation_stats: List[Dict]):
        """
        Сохраняет полный отчет в Markdown формате
        """
        report_lines = []
        
        # Заголовок
        report_lines.append(f"# Отчет об оптимизации PostgreSQL")
        report_lines.append(f"\n**Дата и время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**ID сессии:** {self.session_id}")
        report_lines.append("\n---\n")
        
        # 1. Конфигурация эксперимента
        report_lines.append("## 1. Конфигурация эксперимента\n")
        
        # Загружаем конфиги из оригинальных файлов
        try:
            from . import config
            ga_cfg = config.GA_CONFIG
            fitness_cfg = config.FITNESS_CONFIG
            
            report_lines.append("### Параметры генетического алгоритма")
            report_lines.append(self.formatter.dict_to_table(ga_cfg, None))
            
            report_lines.append("\n### Параметры фитнес-функции")
            report_lines.append(self.formatter.dict_to_table(fitness_cfg, None))
        except:
            pass
        
        # 2. Результаты
        report_lines.append("\n## 2. Результаты эксперимента\n")
        
        # Базовая конфигурация
        if baseline_results:
            report_lines.append(self.formatter.dict_to_table(
                baseline_results.get('load_metrics', {}), 
                "Метрики базовой конфигурации"
            ))
        
        # Лучшая найденная конфигурация
        if optimization_results and 'best_config' in optimization_results:
            report_lines.append(self.formatter.dict_to_table(
                optimization_results['best_config'],
                "Лучшая найденная конфигурация"
            ))
            
            report_lines.append(f"\n**Лучшее значение фитнес-функции:** {optimization_results.get('best_fitness', 0):.4f}")
        
        # Сравнение производительности
        if baseline_results and validation_results:
            metrics_to_compare = ['throughput', 'avg_latency', 'error_rate', 'cpu_percent']
            report_lines.append(self.formatter.comparison_table(
                baseline_results.get('load_metrics', {}),
                validation_results.get('load_metrics', {}),
                metrics_to_compare
            ))
        
        # 3. Статистика по поколениям
        if generation_stats:
            report_lines.append("\n## 3. Статистика по поколениям\n")
            
            # Форматируем данные для таблицы
            gen_data = []
            for stats in generation_stats:
                gen_data.append({
                    'Поколение': stats.get('generation', 0),
                    'Средний fitness': stats.get('avg_fitness', 0),
                    'Макс. fitness': stats.get('max_fitness', 0),
                    'Мин. fitness': stats.get('min_fitness', 0),
                    'Std dev': stats.get('std_fitness', 0)
                })
            
            report_lines.append(self.formatter.list_to_table(gen_data, None))
        
        # 4. Детальный лог сессии
        report_lines.append("\n## 4. Детальный лог оптимизации\n")
        
        # Группируем логи по поколениям
        report_lines.append("```")
        for log_entry in self.session_log:
            if "Поколение" in log_entry['message'] and "Особь" in log_entry['message']:
                report_lines.append(f"\n{log_entry['timestamp']} - {log_entry['message']}")
            elif "Фитнес:" in log_entry['message'] or "Throughput:" in log_entry['message']:
                report_lines.append(f"  {log_entry['message'].strip()}")
            else:
                report_lines.append(f"{log_entry['timestamp']} - {log_entry['message']}")
        report_lines.append("```")
        
        # 5. Итоговые выводы
        report_lines.append("\n## 5. Выводы\n")
        
        if baseline_results and validation_results:
            baseline_tp = baseline_results.get('load_metrics', {}).get('throughput', 0)
            best_tp = validation_results.get('load_metrics', {}).get('throughput', 0)
            
            if baseline_tp > 0:
                improvement = ((best_tp - baseline_tp) / baseline_tp) * 100
                report_lines.append(f"- **Улучшение пропускной способности:** {improvement:+.1f}%")
            
            baseline_latency = baseline_results.get('load_metrics', {}).get('avg_latency', 0)
            best_latency = validation_results.get('load_metrics', {}).get('avg_latency', 0)
            
            if baseline_latency > 0:
                latency_reduction = ((baseline_latency - best_latency) / baseline_latency) * 100
                report_lines.append(f"- **Снижение задержки:** {latency_reduction:+.1f}%")
        
        # Сохраняем отчет
        report_file = self.logs_dir / f"report_{self.session_id}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        print(f"\nMarkdown отчет сохранен: {report_file}")
        return report_file
    
    def save_csv_log(self):
        """Сохраняет лог в CSV формате"""
        if not self.session_log:
            return
        
        csv_file = self.logs_dir / f"log_{self.session_id}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'level', 'message'])
            writer.writeheader()
            writer.writerows(self.session_log)
        
        print(f"CSV лог сохранен: {csv_file}")
        return csv_file
    
    def save_json_summary(self, summary_data: Dict):
        """Сохраняет сводку результатов в JSON формате"""
        json_file = self.logs_dir / f"summary_{self.session_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON сводка сохранена: {json_file}")
        return json_file


# Создаем глобальный экземпляр для использования во всем приложении
experiment_logger = None


def get_logger():
    """Возвращает глобальный экземпляр логгера"""
    global experiment_logger
    if experiment_logger is None:
        experiment_logger = ExperimentLogger()
    return experiment_logger