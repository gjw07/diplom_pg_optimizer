"""
Скрипт для анализа и визуализации результатов экспериментов.
Реализует Этап 6 из Плана 2.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from typing import Dict, List
import numpy as np

from . import config
# Настройка стиля графиков
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class ResultsAnalyzer:
    """
    Класс для анализа результатов оптимизации.
    """
    
    def __init__(self, results_dir: str):
        """
        Инициализация анализатора.
        
        Args:
            results_dir: Директория с результатами экспериментов
        """
        self.results_dir = results_dir
        self.plots_dir = os.path.join(results_dir, 'plots')
        os.makedirs(self.plots_dir, exist_ok=True)
    
    def load_optimization_data(self) -> pd.DataFrame:
        """
        Загружает данные оптимизации из CSV файла.
        
        Returns:
            pd.DataFrame: Данные оптимизации
        """
        # Находим последний файл с результатами
        csv_files = [f for f in os.listdir(self.results_dir) if f.startswith('optimization_') and f.endswith('.csv')]
        if not csv_files:
            print("Файлы с результатами не найдены")
            return pd.DataFrame()
        
        latest_file = sorted(csv_files)[-1]
        filepath = os.path.join(self.results_dir, latest_file)
        
        df = pd.read_csv(filepath)
        print(f"Загружены данные из: {latest_file}")
        print(f"Всего записей: {len(df)}")
        
        return df
    
    def load_baseline_data(self) -> Dict:
        """
        Загружает данные базовой конфигурации.
        
        Returns:
            Dict: Данные baseline
        """
        baseline_file = os.path.join(self.results_dir, 'baseline.json')
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r') as f:
                return json.load(f)
        return {}
    
    def plot_convergence(self, df: pd.DataFrame):
        """
        Строит график сходимости фитнес-функции.
        """
        plt.figure(figsize=(12, 6))
        
        # Группируем по поколениям и считаем статистику
        gen_stats = df.groupby('generation')['fitness'].agg(['mean', 'max', 'min', 'std']).reset_index()
        
        # График сходимости
        plt.subplot(1, 2, 1)
        plt.plot(gen_stats['generation'], gen_stats['max'], 'b-', label='Max fitness', linewidth=2)
        plt.plot(gen_stats['generation'], gen_stats['mean'], 'g--', label='Mean fitness', linewidth=2)
        plt.fill_between(gen_stats['generation'], 
                        gen_stats['mean'] - gen_stats['std'],
                        gen_stats['mean'] + gen_stats['std'],
                        alpha=0.2, color='g', label='±1 std')
        plt.xlabel('Поколение')
        plt.ylabel('Fitness')
        plt.title('Сходимость генетического алгоритма')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Box plot распределения fitness по поколениям
        plt.subplot(1, 2, 2)
        data_to_plot = [df[df['generation'] == gen]['fitness'].values 
                       for gen in sorted(df['generation'].unique())]
        plt.boxplot(data_to_plot, labels=sorted(df['generation'].unique()))
        plt.xlabel('Поколение')
        plt.ylabel('Fitness')
        plt.title('Распределение fitness по поколениям')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, 'convergence.png'), dpi=150)
        plt.show()
    
    def plot_performance_comparison(self, df: pd.DataFrame, baseline: Dict):
        """
        Строит график сравнения производительности.
        """
        # Находим лучшую конфигурацию
        best_idx = df['fitness'].idxmax()
        best_config = df.loc[best_idx]
        
        # Создаем DataFrame для сравнения
        comparison = pd.DataFrame({
            'Метрика': ['Throughput (TPS)', 'Avg Latency (ms)', 'Error Rate (%)', 'CPU Usage (%)'],
            'Baseline': [
                baseline.get('load_metrics', {}).get('throughput', 0),
                baseline.get('load_metrics', {}).get('avg_latency', 0),
                baseline.get('load_metrics', {}).get('error_rate', 0) * 100,
                baseline.get('system_metrics', {}).get('cpu_percent', 0)
            ],
            'Optimized': [
                best_config['throughput'],
                best_config['avg_latency'],
                best_config['error_rate'] * 100,
                best_config['cpu_usage']
            ]
        })
        
        # Нормализуем для лучшего отображения
        for metric in comparison['Метрика']:
            max_val = max(comparison.loc[comparison['Метрика'] == metric, ['Baseline', 'Optimized']].values.max())
            if max_val > 0:
                comparison.loc[comparison['Метрика'] == metric, 'Baseline'] /= max_val
                comparison.loc[comparison['Метрика'] == metric, 'Optimized'] /= max_val
        
        # Строим радарную диаграмму
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='polar')
        
        categories = list(comparison['Метрика'])
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        
        values_baseline = list(comparison['Baseline']) + [comparison['Baseline'].iloc[0]]
        values_optimized = list(comparison['Optimized']) + [comparison['Optimized'].iloc[0]]
        
        ax.plot(angles, values_baseline, 'o-', linewidth=2, label='Baseline', color='red')
        ax.fill(angles, values_baseline, alpha=0.1, color='red')
        ax.plot(angles, values_optimized, 'o-', linewidth=2, label='Optimized', color='green')
        ax.fill(angles, values_optimized, alpha=0.1, color='green')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=10)
        ax.set_ylim(0, 1)
        plt.title('Сравнение производительности (нормализованные метрики)', size=14, pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, 'performance_radar.png'), dpi=150)
        plt.show()
    
    def plot_parameter_evolution(self, df: pd.DataFrame):
        """
        Строит графики эволюции параметров.
        """
        param_cols = [col for col in df.columns if col in config.OPTIMIZABLE_PARAMS.keys()]
        
        if not param_cols:
            print("Параметры не найдены в данных")
            return
        
        n_params = len(param_cols)
        fig, axes = plt.subplots(n_params, 1, figsize=(12, 4 * n_params))
        if n_params == 1:
            axes = [axes]
        
        for i, param in enumerate(param_cols):
            ax = axes[i]
            
            # Группируем по поколениям
            param_stats = df.groupby('generation')[param].agg(['mean', 'std']).reset_index()
            
            # Линейный график средних значений
            ax.plot(param_stats['generation'], param_stats['mean'], 'b-', linewidth=2, label='Mean value')
            ax.fill_between(param_stats['generation'],
                           param_stats['mean'] - param_stats['std'],
                           param_stats['mean'] + param_stats['std'],
                           alpha=0.2, color='b', label='±1 std')
            
            # Добавляем точки для всех особей
            ax.scatter(df['generation'], df[param], alpha=0.3, color='gray', s=30, label='All individuals')
            
            # Отмечаем границы
            param_info = config.OPTIMIZABLE_PARAMS[param]
            ax.axhline(y=param_info['min'], color='r', linestyle='--', alpha=0.5, label='Min')
            ax.axhline(y=param_info['max'], color='r', linestyle='--', alpha=0.5, label='Max')
            
            ax.set_xlabel('Поколение')
            ax.set_ylabel(f'{param} ({param_info.get("unit", "")})')
            ax.set_title(f'Эволюция параметра: {param}\n{param_info["description"]}')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, 'parameter_evolution.png'), dpi=150)
        plt.show()
    
    def generate_report(self):
        """
        Генерирует полный отчет по результатам эксперимента.
        """
        print("\n" + "=" * 60)
        print("АНАЛИЗ РЕЗУЛЬТАТОВ ЭКСПЕРИМЕНТА")
        print("=" * 60)
        
        # Загружаем данные
        df = self.load_optimization_data()
        baseline = self.load_baseline_data()
        
        if df.empty:
            print("Нет данных для анализа")
            return
        
        # Основная статистика
        print("\n1. ОБЩАЯ СТАТИСТИКА:")
        print(f"   - Всего оцененных конфигураций: {len(df)}")
        print(f"   - Количество поколений: {df['generation'].nunique()}")
        print(f"   - Размер популяции: {len(df) // df['generation'].nunique()}")
        
        # Лучшая конфигурация
        best_idx = df['fitness'].idxmax()
        best_config = df.loc[best_idx]
        print(f"\n2. ЛУЧШАЯ КОНФИГУРАЦИЯ (Fitness = {best_config['fitness']:.4f}):")
        for param in config.OPTIMIZABLE_PARAMS.keys():
            if param in best_config:
                unit = config.OPTIMIZABLE_PARAMS[param].get('unit', '')
                print(f"   - {param}: {best_config[param]} {unit}")
        
        # Метрики лучшей конфигурации
        print(f"\n3. МЕТРИКИ ЛУЧШЕЙ КОНФИГУРАЦИИ:")
        print(f"   - Throughput: {best_config['throughput']:.2f} TPS")
        print(f"   - Avg Latency: {best_config['avg_latency']:.2f} ms")
        print(f"   - Error Rate: {best_config['error_rate']*100:.2f}%")
        print(f"   - CPU Usage: {best_config['cpu_usage']:.1f}%")
        
        # Сравнение с baseline
        if baseline:
            baseline_tp = baseline.get('load_metrics', {}).get('throughput', 0)
            baseline_latency = baseline.get('load_metrics', {}).get('avg_latency', 0)
            
            improvement_tp = ((best_config['throughput'] - baseline_tp) / baseline_tp * 100) if baseline_tp > 0 else 0
            reduction_latency = ((baseline_latency - best_config['avg_latency']) / baseline_latency * 100) if baseline_latency > 0 else 0
            
            print(f"\n4. СРАВНЕНИЕ С БАЗОВОЙ КОНФИГУРАЦИЕЙ:")
            print(f"   - Улучшение пропускной способности: {improvement_tp:.1f}%")
            print(f"   - Снижение задержки: {reduction_latency:.1f}%")
        
        print("\n" + "=" * 60)
        
        # Генерация графиков
        print("\nГенерация графиков...")
        self.plot_convergence(df)
        if baseline:
            self.plot_performance_comparison(df, baseline)
        self.plot_parameter_evolution(df)
        print(f"Графики сохранены в: {self.plots_dir}")


def analyze():
    """
    Запуск анализа результатов.
    """
    analyzer = ResultsAnalyzer(config.PATHS['RESULTS_DIR'])
    analyzer.generate_report()



if __name__ == "__main__":
    analyze()