#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Графический вьювер для просмотра результатов оптимизации PostgreSQL
Автоматически загружает последние результаты из папки experiment_results
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter import font as tkfont
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import glob

# Настройка стиля matplotlib
plt.style.use('seaborn-v0_8-darkgrid')


class ResultsViewer:
    """Графический интерфейс для просмотра результатов оптимизации"""
    
    def __init__(self, results_dir: str = None):
        # Делаем дефолтный путь независимым от текущей рабочей директории:
        # ожидаем `experiment_results` в корне проекта (рядом с папкой `pg_optimizer`).
        default_results_dir = Path(__file__).resolve().parent.parent / "experiment_results"
        self.results_dir = Path(results_dir) if results_dir else default_results_dir
        self.current_data = None
        self.baseline_data = None
        self.validation_data = None
        self.summary_data = None
        self.best_configs = []
        self.current_csv_file = None
        self.current_json_file = None
        
        # Создаем главное окно
        self.root = tk.Tk()
        self.root.title("PG Optimizer - Анализ результатов")
        self.root.geometry("1550x900")
        
        # Устанавливаем минимальный размер
        self.root.minsize(1200, 700)

        # Увеличиваем масштаб интерфейса (особенно полезно на HiDPI/Windows)
        try:
            self.root.tk.call("tk", "scaling", 1.4)
        except Exception:
            pass

        # Увеличиваем системные шрифты Tk, чтобы выросли вкладки/диалоги/лейблы (не только ttk-стили)
        try:
            for name, size, weight in [
                ("TkDefaultFont", 11, "normal"),
                ("TkTextFont", 11, "normal"),
                ("TkFixedFont", 11, "normal"),
                ("TkHeadingFont", 12, "bold"),
                ("TkMenuFont", 11, "normal"),
                ("TkCaptionFont", 11, "normal"),
                ("TkSmallCaptionFont", 10, "normal"),
                ("TkIconFont", 11, "normal"),
                ("TkTooltipFont", 10, "normal"),
            ]:
                f = tkfont.nametofont(name)
                f.configure(size=size, weight=weight)
        except Exception:
            pass
        
        # Стили
        self.setup_styles()
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Загружаем данные
        self.load_latest_data()
        
    def setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветов
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Error.TLabel', foreground='red')

        # Крупнее базовые элементы
        style.configure('TButton', font=('Arial', 12), padding=(14, 8))
        style.configure('TLabel', font=('Arial', 12))
        style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'))
        style.configure('Treeview', font=('Arial', 11), rowheight=30)
        style.configure('Treeview.Heading', font=('Arial', 12, 'bold'))

        # Вкладки: крупнее и с отступами
        style.configure('TNotebook.Tab', font=('Arial', 12, 'bold'), padding=(14, 10))
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Главный контейнер с прокруткой
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        
        # Верхняя панель с информацией
        self.create_header(main_frame)
        
        # Информационная панель о текущем файле
        self.create_info_panel(main_frame)
        
        # Панель с вкладками
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Вкладки
        self.create_best_configs_tab()
        self.create_comparison_tab()
        self.create_detailed_analysis_tab()
        self.create_evolution_tab()
        self.create_log_tab()
        
        # Статус бар
        self.create_status_bar()
        
    def create_header(self, parent):
        """Создание верхней панели"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Заголовок
        title_label = ttk.Label(header_frame, text="Анализ результатов оптимизации PostgreSQL", 
                                style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Кнопки управления
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT)
        
        refresh_btn = ttk.Button(button_frame, text="Обновить", command=self.load_latest_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        open_btn = ttk.Button(button_frame, text="Открыть файл", command=self.open_file_dialog)
        open_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(button_frame, text="Экспорт отчета", command=self.export_report)
        export_btn.pack(side=tk.LEFT, padx=5)
        
    def create_info_panel(self, parent):
        """Создание информационной панели"""
        self.info_frame = ttk.LabelFrame(parent, text="Информация о текущем файле")
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = ttk.Label(self.info_frame, text="Файлы не загружены", font=('Arial', 11))
        self.info_label.pack(padx=10, pady=5, anchor=tk.W)
        
    def create_status_bar(self):
        """Создание статус бара"""
        self.status_bar = ttk.Label(self.root, text="Готов", relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 11))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_best_configs_tab(self):
        """Создание вкладки с лучшими конфигурациями"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Лучшие конфигурации")
        
        # Создаем разделитель
        paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - список конфигураций
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Топ конфигураций", style='Header.TLabel').pack(pady=5)
        
        # Список с прокруткой
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.config_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 12),
            activestyle='dotbox',
            selectmode=tk.SINGLE,
        )
        self.config_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.config_listbox.yview)
        
        self.config_listbox.bind('<<ListboxSelect>>', self.on_config_select)
        
        # Правая панель - детали конфигурации
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # Текстовое поле для деталей
        self.config_details = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, font=('Consolas', 12)
        )
        self.config_details.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка копирования
        copy_btn = ttk.Button(right_frame, text="Копировать в буфер", 
                              command=self.copy_config_to_clipboard)
        copy_btn.pack(pady=5)
        
    def create_comparison_tab(self):
        """Создание вкладки сравнения"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Сравнение с базовой")
        
        # Создаем фрейм для графиков
        self.comparison_frame = ttk.Frame(tab)
        self.comparison_frame.pack(fill=tk.BOTH, expand=True)
        
        # Текстовое поле для вывода сравнения
        self.comparison_text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, font=('Consolas', 12), height=10
        )
        self.comparison_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
    def create_detailed_analysis_tab(self):
        """Создание вкладки детального анализа"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Детальный анализ")

        # Панели: слева сравнение по параметрам, справа детали по клику
        paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=2)
        paned.add(right, weight=3)

        ttk.Label(left, text="ТОП-конфигурации по параметрам", style='Header.TLabel').pack(
            anchor=tk.W, pady=(0, 8)
        )

        cols = ("param", "pick", "value", "tp", "lat", "err", "fitness")
        self.param_tree = ttk.Treeview(left, columns=cols, show="headings")
        self.param_tree.heading("param", text="Параметр")
        self.param_tree.heading("pick", text="Конфиг")
        self.param_tree.heading("value", text="Значение")
        self.param_tree.heading("tp", text="Δ TP")
        self.param_tree.heading("lat", text="Δ Lat")
        self.param_tree.heading("err", text="Δ Err")
        self.param_tree.heading("fitness", text="Fitness")

        self.param_tree.column("param", width=190, anchor=tk.W)
        self.param_tree.column("pick", width=95, anchor=tk.CENTER)
        self.param_tree.column("value", width=110, anchor=tk.E)
        self.param_tree.column("tp", width=90, anchor=tk.E)
        self.param_tree.column("lat", width=90, anchor=tk.E)
        self.param_tree.column("err", width=90, anchor=tk.E)
        self.param_tree.column("fitness", width=90, anchor=tk.E)

        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.param_tree.yview)
        self.param_tree.configure(yscrollcommand=yscroll.set)
        self.param_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.param_tree.bind("<<TreeviewSelect>>", self.on_param_row_select)

        ttk.Label(right, text="Детали и компромиссы", style='Header.TLabel').pack(
            anchor=tk.W, pady=(0, 8)
        )
        self.analysis_text = scrolledtext.ScrolledText(right, wrap=tk.WORD, font=('Consolas', 12))
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
    def create_evolution_tab(self):
        """Создание вкладки эволюции"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Эволюция параметров")
        
        # Фрейм для графика
        self.evolution_frame = ttk.Frame(tab)
        self.evolution_frame.pack(fill=tk.BOTH, expand=True)
        
    def create_log_tab(self):
        """Создание вкладки с логами"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Лог оптимизации")
        
        # Фрейм с выбором лога
        log_control_frame = ttk.Frame(tab)
        log_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(log_control_frame, text="Лог-файл:").pack(side=tk.LEFT)
        
        self.log_file_var = tk.StringVar()
        self.log_combo = ttk.Combobox(log_control_frame, textvariable=self.log_file_var, width=50)
        self.log_combo.pack(side=tk.LEFT, padx=5)
        self.log_combo.bind('<<ComboboxSelected>>', self.on_log_select)
        
        self.log_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, font=('Consolas', 11))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def load_latest_data(self):
        """Автоматическая загрузка последних данных"""
        self.update_status("Поиск последних результатов...")
        
        # Поиск последнего CSV файла
        csv_files = sorted(self.results_dir.glob("optimization_*.csv"), key=os.path.getctime, reverse=True)
        
        if csv_files:
            self.current_csv_file = csv_files[0]
            self.update_status(f"Загрузка: {self.current_csv_file.name}")
            self.load_csv_data(self.current_csv_file)
        else:
            self.update_status("CSV файлы не найдены")
            self.current_data = None
        
        # Поиск последнего JSON файла со сводкой
        json_files = sorted(self.results_dir.glob("logs/summary_*.json"), key=os.path.getctime, reverse=True)
        if json_files:
            self.current_json_file = json_files[0]
            self.load_json_data(self.current_json_file)
        
        # Загрузка baseline
        baseline_file = self.results_dir / "baseline.json"
        if baseline_file.exists():
            self.load_baseline_data(baseline_file)
        
        # Загрузка validation
        validation_file = self.results_dir / "validation.json"
        if validation_file.exists():
            self.load_validation_data(validation_file)
        
        # Обновляем список логов
        self.update_log_list()
        
        # Обновляем интерфейс
        if self.current_data is not None:
            self.prepare_best_configs()
            self.update_ui()
            self.update_info_panel()
            self.update_status(f"Загружено: {len(self.current_data)} записей")
        else:
            self.update_status("Нет данных для отображения. Запустите оптимизацию или откройте файл вручную.")
            self.show_no_data_message()
    
    def load_csv_data(self, filepath):
        """Загрузка CSV файла с результатами"""
        try:
            self.current_data = pd.read_csv(filepath)
            print(f"Загружены данные из: {filepath}")
            print(f"Всего записей: {len(self.current_data)}")
            return True
        except Exception as e:
            print(f"Ошибка загрузки CSV: {e}")
            self.current_data = None
            return False
    
    def load_json_data(self, filepath):
        """Загрузка JSON файла со сводкой"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.summary_data = json.load(f)
            print(f"Загружена сводка из: {filepath}")
            return True
        except Exception as e:
            print(f"Ошибка загрузки JSON: {e}")
            return False
    
    def load_baseline_data(self, filepath):
        """Загрузка baseline данных"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.baseline_data = json.load(f)
            print(f"Загружены baseline данные")
            return True
        except Exception as e:
            print(f"Ошибка загрузки baseline: {e}")
            return False
    
    def load_validation_data(self, filepath):
        """Загрузка validation данных"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.validation_data = json.load(f)
            print(f"Загружены validation данные")
            return True
        except Exception as e:
            print(f"Ошибка загрузки validation: {e}")
            return False
    
    def update_log_list(self):
        """Обновление списка лог-файлов"""
        log_files = sorted(self.results_dir.glob("logs/log_*.csv"), key=os.path.getctime, reverse=True)
        log_names = [f.name for f in log_files]
        
        self.log_combo['values'] = log_names
        if log_names:
            self.log_combo.set(log_names[0])
            self.load_log_file(log_files[0])
    
    def load_log_file(self, filepath):
        """Загрузка лог-файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, content)
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Ошибка загрузки лога: {e}")
    
    def on_log_select(self, event):
        """Обработчик выбора лог-файла"""
        selected = self.log_combo.get()
        if selected:
            filepath = self.results_dir / "logs" / selected
            self.load_log_file(filepath)
    
    def update_info_panel(self):
        """Обновление информационной панели"""
        info_text = []
        
        if self.current_csv_file:
            info_text.append(f"CSV: {self.current_csv_file.name}")
            if self.current_data is not None:
                info_text.append(f" ({len(self.current_data)} записей)")
        
        if self.current_json_file:
            info_text.append(f" | JSON: {self.current_json_file.name}")
        
        if self.baseline_data:
            info_text.append(" | Baseline: загружена")
        
        if self.validation_data:
            info_text.append(" | Validation: загружена")
        
        if info_text:
            self.info_label.config(text="".join(info_text))
        else:
            self.info_label.config(text="Файлы не загружены")
    
    def show_no_data_message(self):
        """Показать сообщение об отсутствии данных"""
        try:
            self.config_details.delete(1.0, tk.END)
            self.config_details.insert(tk.END, "Нет данных для отображения.\n\n")
            self.config_details.insert(tk.END, "Возможные причины:\n")
            self.config_details.insert(tk.END, "  1. Оптимизация еще не запускалась\n")
            self.config_details.insert(tk.END, "  2. Результаты сохранены в другой директории\n\n")
            self.config_details.insert(tk.END, "Действия:\n")
            self.config_details.insert(tk.END, "  - Нажмите 'Открыть файл' для выбора CSV файла с результатами\n")
            self.config_details.insert(tk.END, "  - Запустите оптимизацию: python -m pg_optimizer.run_experiment\n")
        except:
            pass
        
        try:
            self.comparison_text.delete(1.0, tk.END)
            self.comparison_text.insert(tk.END, "Нет данных для сравнения")
        except:
            pass
        
        try:
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, "Нет данных для анализа")
        except:
            pass
    
    def open_file_dialog(self):
        """Открытие диалога выбора файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл с результатами",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self.results_dir
        )
        
        if file_path:
            self.current_csv_file = Path(file_path)
            self.results_dir = self.current_csv_file.parent

            if self.load_csv_data(self.current_csv_file):
                self.current_json_file = None
                self.summary_data = None
                self.baseline_data = None
                self.validation_data = None

                json_files = sorted(self.results_dir.glob("logs/summary_*.json"), key=os.path.getctime, reverse=True)
                if json_files:
                    self.current_json_file = json_files[0]
                    self.load_json_data(self.current_json_file)

                baseline_file = self.results_dir / "baseline.json"
                if baseline_file.exists():
                    self.load_baseline_data(baseline_file)

                validation_file = self.results_dir / "validation.json"
                if validation_file.exists():
                    self.load_validation_data(validation_file)

                self.update_log_list()
                self.prepare_best_configs()
                self.update_ui()
                self.update_info_panel()
                self.update_status(f"Загружен файл: {Path(file_path).name}")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить файл")
    
    def _calculate_fitness_from_metrics(self, load_metrics , system_metrics) -> float:
        """Вычисляет fitness на основе метрик"""
        tp = load_metrics.get('throughput', 0)
        latency = load_metrics.get('avg_latency', 100)
        error_rate = load_metrics.get('error_rate', 0)
        cpu = system_metrics.get('cpu_percent', 50)
        
        if self.baseline_data:
            baseline_tp = self.baseline_data.get('load_metrics', {}).get('throughput', 1)
            baseline_latency = self.baseline_data.get('load_metrics', {}).get('avg_latency', 1)
            tp_score = tp / baseline_tp if baseline_tp > 0 else 0
            latency_score = baseline_latency / max(latency, 0.1)
        else:
            tp_score = tp / 150
            latency_score = 100 / max(latency, 0.1)
        
        tp_score = min(tp_score, 2.0)
        latency_score = min(latency_score, 2.0)
        cpu_penalty = cpu / 100.0
        
        fitness = (tp_score * 0.6) + (latency_score * 0.3) - (cpu_penalty * 0.1)
        return max(fitness, 0.0)
    
    def prepare_best_configs(self):
        """Подготовка списка лучших конфигураций"""
        self.best_configs = []
        
        if self.current_data is not None and 'fitness' in self.current_data.columns:
            top_configs = self.current_data.nlargest(5, 'fitness')
            
            for idx, row in top_configs.iterrows():
                config = {}
                param_cols = [col for col in self.current_data.columns 
                             if col not in ['generation', 'individual', 'fitness', 
                                          'throughput', 'avg_latency', 'error_rate', 
                                          'cpu_usage', 'memory_usage']]
                
                for col in param_cols:
                    config[col] = row[col]
                
                metrics = {
                    'fitness': row['fitness'],
                    'throughput': row['throughput'],
                    'avg_latency': row['avg_latency'],
                    'error_rate': row['error_rate'],
                    'cpu_usage': row['cpu_usage']
                }
                
                self.best_configs.append({
                    'rank': len(self.best_configs) + 1,
                    'config': config,
                    'metrics': metrics,
                    'generation': row['generation'],
                    'is_validation': False
                })
        
        # Добавляем конфигурацию из валидации (шаг 7)
        if self.validation_data:
            val_config = self.validation_data.get('config', {})
            val_metrics = self.validation_data.get('load_metrics', {})
            val_system = self.validation_data.get('system_metrics', {})
            
            validation_entry = {
                'rank': '⭐ ВАЛИДАЦИЯ',
                'config': val_config,
                'metrics': {
                    'fitness': self._calculate_fitness_from_metrics(val_metrics, val_system),
                    'throughput': val_metrics.get('throughput', 0),
                    'avg_latency': val_metrics.get('avg_latency', 0),
                    'error_rate': val_metrics.get('error_rate', 0),
                    'cpu_usage': val_system.get('cpu_percent', 0)
                },
                'generation': 'Валидация',
                'is_validation': True
            }
            
            self.best_configs.insert(0, validation_entry)
    
    def update_ui(self):
        """Обновление пользовательского интерфейса"""
        self.update_best_configs_list()
        self.update_comparison_tab()
        self.update_detailed_analysis()
        self.update_evolution_graph()

    def _safe_float(self, x):
        try:
            if x is None:
                return None
            if isinstance(x, (int, float)):
                return float(x)
            return float(str(x).strip())
        except Exception:
            return None

    def _format_delta_pct(self, value):
        if value is None:
            return "—"
        try:
            return f"{value:+.1f}%"
        except Exception:
            return "—"

    def _compute_deltas_vs_baseline(self, metrics):
        if not self.baseline_data:
            return None, None, None

        base_tp = self.baseline_data.get("load_metrics", {}).get("throughput", 0) or 0
        base_lat = self.baseline_data.get("load_metrics", {}).get("avg_latency", 0) or 0
        base_err = self.baseline_data.get("load_metrics", {}).get("error_rate", 0) or 0

        tp = metrics.get("throughput", 0) or 0
        lat = metrics.get("avg_latency", 0) or 0
        err = metrics.get("error_rate", 0) or 0

        d_tp = ((tp - base_tp) / base_tp * 100) if base_tp > 0 else None
        d_lat = ((base_lat - lat) / base_lat * 100) if base_lat > 0 else None
        d_err = ((base_err - err) / base_err * 100) if base_err > 0 else None
        return d_tp, d_lat, d_err

    def _pct_change(self, base, value):
        try:
            if base is None or value is None:
                return None
            base = float(base)
            value = float(value)
            if base == 0:
                return None
            return (value - base) / base * 100
        except Exception:
            return None

    def on_param_row_select(self, event):
        selection = self.param_tree.selection()
        if not selection:
            return
        iid = selection[0]
        info = getattr(self, "_param_row_map", {}).get(iid)
        if not info:
            return

        param = info["param"]
        mode = info["mode"]
        cfg = info["config_data"]

        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, f"Параметр: {param}\n")
        self.analysis_text.insert(tk.END, f"Кейс среди ТОП-а: {mode}\n")
        self.analysis_text.insert(tk.END, "=" * 60 + "\n\n")

        m = cfg.get("metrics", {}) or {}
        self.analysis_text.insert(tk.END, "Метрики конфигурации:\n")
        self.analysis_text.insert(tk.END, f"  Rank: #{cfg.get('rank', '?')}\n")
        self.analysis_text.insert(tk.END, f"  Fitness: {m.get('fitness', 0):.4f}\n")
        self.analysis_text.insert(tk.END, f"  Throughput: {m.get('throughput', 0):.2f} TPS\n")
        self.analysis_text.insert(tk.END, f"  Avg Latency: {m.get('avg_latency', 0):.2f} ms\n")
        self.analysis_text.insert(tk.END, f"  Error Rate: {m.get('error_rate', 0)*100:.2f}%\n")
        self.analysis_text.insert(tk.END, f"  CPU Usage: {m.get('cpu_usage', 0):.1f}%\n\n")

        val = (cfg.get("config") or {}).get(param)
        self.analysis_text.insert(tk.END, f"Значение параметра: {param} = {val}\n\n")

        d_tp, d_lat, d_err = self._compute_deltas_vs_baseline(m)
        if self.baseline_data:
            self.analysis_text.insert(tk.END, "Эффект относительно baseline:\n")
            self.analysis_text.insert(tk.END, f"  Δ Throughput: {self._format_delta_pct(d_tp)}\n")
            self.analysis_text.insert(tk.END, f"  Δ Latency (↓ лучше): {self._format_delta_pct(d_lat)}\n")
            self.analysis_text.insert(tk.END, f"  Δ Error rate (↓ лучше): {self._format_delta_pct(d_err)}\n\n")
        else:
            self.analysis_text.insert(tk.END, "Baseline не загружен — Δ метрики недоступны.\n\n")

        if self.best_configs:
            best = self.best_configs[0]
            bm = best.get("metrics", {}) or {}
            self.analysis_text.insert(tk.END, "Компромиссы относительно лучшей по fitness (из ТОП-а):\n")
            self.analysis_text.insert(
                tk.END,
                f"  Throughput: {self._format_delta_pct(self._pct_change(bm.get('throughput', 0), m.get('throughput', 0)))}\n"
            )
            self.analysis_text.insert(
                tk.END,
                f"  Latency: {self._format_delta_pct(self._pct_change(bm.get('avg_latency', 0), m.get('avg_latency', 0)))} (плюс = хуже)\n"
            )
            self.analysis_text.insert(
                tk.END,
                f"  Error rate: {self._format_delta_pct(self._pct_change(bm.get('error_rate', 0), m.get('error_rate', 0)))} (плюс = хуже)\n\n"
            )

        self.analysis_text.insert(tk.END, "Как использовать это на практике:\n")
        self.analysis_text.insert(tk.END, "  - Смотри на строки (высокий/низкий) и выбирай те, где нужные метрики улучшаются.\n")
        self.analysis_text.insert(tk.END, "  - Переноси 1–2 параметра из выбранного кейса в свою конфигурацию и проверяй нагрузкой.\n")
    
    def update_best_configs_list(self):
        """Обновление списка лучших конфигураций"""
        self.config_listbox.delete(0, tk.END)
        
        for config in self.best_configs:
            metrics = config['metrics']
            if config.get('is_validation', False):
                display_text = f"⭐ {config['rank']} | Fitness: {metrics['fitness']:.4f} | TP: {metrics['throughput']:.0f} TPS ⭐"
                self.config_listbox.insert(tk.END, display_text)
            else:
                display_text = f"#{config['rank']} | Fitness: {metrics['fitness']:.4f} | TP: {metrics['throughput']:.0f} TPS"
                self.config_listbox.insert(tk.END, display_text)
        
        if self.best_configs:
            self.config_listbox.selection_set(0)
            self.show_config_details(self.best_configs[0])
    
    def on_config_select(self, event):
        selection = self.config_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.best_configs):
            self.show_config_details(self.best_configs[idx])
    
    def show_config_details(self, config_data):
        """Отображение деталей выбранной конфигурации"""
        self.config_details.delete(1.0, tk.END)
        
        if config_data.get('is_validation', False):
            self.config_details.insert(tk.END, f"⭐ ЛУЧШАЯ КОНФИГУРАЦИЯ (ПОСЛЕ ВАЛИДАЦИИ) ⭐\n")
        else:
            self.config_details.insert(tk.END, f"КОНФИГУРАЦИЯ #{config_data['rank']}\n")
        self.config_details.insert(tk.END, "=" * 50 + "\n\n")
        
        self.config_details.insert(tk.END, "ПАРАМЕТРЫ PostgreSQL:\n")
        self.config_details.insert(tk.END, "-" * 30 + "\n")
        for param, value in config_data['config'].items():
            self.config_details.insert(tk.END, f"  {param}: {value}\n")
        
        self.config_details.insert(tk.END, "\nМЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ:\n")
        self.config_details.insert(tk.END, "-" * 30 + "\n")
        metrics = config_data['metrics']
        self.config_details.insert(tk.END, f"  Fitness: {metrics['fitness']:.4f}\n")
        self.config_details.insert(tk.END, f"  Throughput: {metrics['throughput']:.2f} TPS\n")
        self.config_details.insert(tk.END, f"  Avg Latency: {metrics['avg_latency']:.2f} ms\n")
        self.config_details.insert(tk.END, f"  Error Rate: {metrics['error_rate']*100:.2f}%\n")
        self.config_details.insert(tk.END, f"  CPU Usage: {metrics['cpu_usage']:.1f}%\n")
        
        if config_data.get('is_validation', False):
            self.config_details.insert(tk.END, f"\n✅ Получена после валидации (шаг 7)\n")
        else:
            self.config_details.insert(tk.END, f"\nНайдена в поколении: {config_data['generation']}\n")
        
        if self.baseline_data:
            self.config_details.insert(tk.END, "\nАНАЛИЗ УЛУЧШЕНИЙ ОТНОСИТЕЛЬНО BASELINE:\n")
            self.config_details.insert(tk.END, "-" * 30 + "\n")
            
            baseline_tp = self.baseline_data.get('load_metrics', {}).get('throughput', 0)
            if baseline_tp > 0:
                improvement = ((metrics['throughput'] - baseline_tp) / baseline_tp) * 100
                if improvement > 0:
                    self.config_details.insert(tk.END, f"  + Улучшение пропускной способности: {improvement:+.1f}%\n")
                else:
                    self.config_details.insert(tk.END, f"  - Ухудшение пропускной способности: {improvement:+.1f}%\n")
            
            baseline_latency = self.baseline_data.get('load_metrics', {}).get('avg_latency', 0)
            if baseline_latency > 0:
                latency_change = ((baseline_latency - metrics['avg_latency']) / baseline_latency) * 100
                if latency_change > 0:
                    self.config_details.insert(tk.END, f"  + Снижение задержки: {latency_change:+.1f}%\n")
                else:
                    self.config_details.insert(tk.END, f"  - Увеличение задержки: {latency_change:+.1f}%\n")
    
    def copy_config_to_clipboard(self):
        selection = self.config_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.best_configs):
            config = self.best_configs[idx]['config']
            config_text = json.dumps(config, indent=2, ensure_ascii=False)
            self.root.clipboard_clear()
            self.root.clipboard_append(config_text)
            self.update_status("Конфигурация скопирована в буфер обмена")
    
    def update_comparison_tab(self):
        """Обновление вкладки сравнения"""
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()
        
        if self.best_configs and self.baseline_data:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            metrics_names = ['Throughput\n(TPS)', 'Avg Latency\n(ms)', 'Error Rate\n(%)']
            baseline_values = [
                self.baseline_data.get('load_metrics', {}).get('throughput', 0),
                self.baseline_data.get('load_metrics', {}).get('avg_latency', 0),
                self.baseline_data.get('load_metrics', {}).get('error_rate', 0) * 100
            ]
            
            best_config = self.best_configs[0]
            best_values = [
                best_config['metrics']['throughput'],
                best_config['metrics']['avg_latency'],
                best_config['metrics']['error_rate'] * 100
            ]
            
            x = range(len(metrics_names))
            width = 0.35
            
            ax1.bar([i - width/2 for i in x], baseline_values, width, label='Baseline', alpha=0.8, color='#FF6B6B')
            ax1.bar([i + width/2 for i in x], best_values, width, label='Optimized', alpha=0.8, color='#4ECDC4')
            
            ax1.set_xlabel('Метрики')
            ax1.set_ylabel('Значение')
            ax1.set_title('Сравнение метрик производительности')
            ax1.set_xticks(x)
            ax1.set_xticklabels(metrics_names)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            categories = ['Throughput', 'Latency\n(inverse)', 'Error Rate\n(inverse)', 'Free CPU']
            
            max_vals = [max(baseline_values[0], best_values[0]), 
                       max(baseline_values[1], best_values[1]),
                       100, 100]
            
            baseline_norm = [
                baseline_values[0] / max_vals[0] if max_vals[0] > 0 else 0,
                1 - (baseline_values[1] / max_vals[1] if max_vals[1] > 0 else 0),
                1 - (baseline_values[2] / 100),
                (100 - self.baseline_data.get('system_metrics', {}).get('cpu_percent', 0)) / 100
            ]
            
            best_norm = [
                best_values[0] / max_vals[0] if max_vals[0] > 0 else 0,
                1 - (best_values[1] / max_vals[1] if max_vals[1] > 0 else 0),
                1 - (best_values[2] / 100),
                (100 - best_config['metrics']['cpu_usage']) / 100
            ]
            
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            baseline_norm += baseline_norm[:1]
            best_norm += best_norm[:1]
            angles += angles[:1]
            
            ax2.plot(angles, baseline_norm, 'o-', linewidth=2, label='Baseline', color='#FF6B6B')
            ax2.fill(angles, baseline_norm, alpha=0.25, color='#FF6B6B')
            ax2.plot(angles, best_norm, 'o-', linewidth=2, label='Optimized', color='#4ECDC4')
            ax2.fill(angles, best_norm, alpha=0.25, color='#4ECDC4')
            ax2.set_xticks(angles[:-1])
            ax2.set_xticklabels(categories)
            ax2.set_title('Радарная диаграмма (нормализованные метрики)')
            ax2.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            ax2.set_ylim(0, 1)
            
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.comparison_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.comparison_text.delete(1.0, tk.END)
            self.comparison_text.insert(tk.END, "СРАВНЕНИЕ С БАЗОВОЙ КОНФИГУРАЦИЕЙ\n")
            self.comparison_text.insert(tk.END, "=" * 50 + "\n\n")
            
            baseline_tp = baseline_values[0]
            best_tp = best_values[0]
            if baseline_tp > 0:
                improvement = ((best_tp - baseline_tp) / baseline_tp) * 100
                self.comparison_text.insert(tk.END, f"Пропускная способность:\n")
                self.comparison_text.insert(tk.END, f"  Baseline: {baseline_tp:.2f} TPS\n")
                self.comparison_text.insert(tk.END, f"  Optimized: {best_tp:.2f} TPS\n")
                self.comparison_text.insert(tk.END, f"  Изменение: {improvement:+.1f}%\n\n")
            
            baseline_lat = baseline_values[1]
            best_lat = best_values[1]
            if baseline_lat > 0:
                latency_change = ((baseline_lat - best_lat) / baseline_lat) * 100
                self.comparison_text.insert(tk.END, f"Средняя задержка:\n")
                self.comparison_text.insert(tk.END, f"  Baseline: {baseline_lat:.2f} ms\n")
                self.comparison_text.insert(tk.END, f"  Optimized: {best_lat:.2f} ms\n")
                self.comparison_text.insert(tk.END, f"  Изменение: {latency_change:+.1f}%\n\n")
            
            baseline_err = baseline_values[2]
            best_err = best_values[2]
            self.comparison_text.insert(tk.END, f"Уровень ошибок:\n")
            self.comparison_text.insert(tk.END, f"  Baseline: {baseline_err:.2f}%\n")
            self.comparison_text.insert(tk.END, f"  Optimized: {best_err:.2f}%\n")
            self.comparison_text.insert(tk.END, f"  Изменение: {baseline_err - best_err:+.2f}%\n")
            
            if self.validation_data:
                self.comparison_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                self.comparison_text.insert(tk.END, "ВАЛИДАЦИЯ ЛУЧШЕЙ КОНФИГУРАЦИИ\n")
                self.comparison_text.insert(tk.END, "=" * 50 + "\n")
                
                val_tp = self.validation_data.get('load_metrics', {}).get('throughput', 0)
                val_lat = self.validation_data.get('load_metrics', {}).get('avg_latency', 0)
                
                self.comparison_text.insert(tk.END, f"Throughput: {val_tp:.2f} TPS\n")
                self.comparison_text.insert(tk.END, f"Avg Latency: {val_lat:.2f} ms\n")
                
                if best_tp > 0:
                    val_improvement = ((val_tp - best_tp) / best_tp) * 100
                    self.comparison_text.insert(tk.END, f"Отклонение от ожидаемого: {val_improvement:+.1f}%\n")
    
    def update_detailed_analysis(self):
        """Обновление детального анализа"""
        for iid in self.param_tree.get_children():
            self.param_tree.delete(iid)
        self._param_row_map = {}

        self.analysis_text.delete(1.0, tk.END)

        if not self.best_configs:
            self.analysis_text.insert(tk.END, "Нет данных для анализа.\n")
            self.analysis_text.insert(tk.END, "Загрузите CSV с результатами (и baseline.json рядом, если нужен расчёт Δ).\n")
            return

        params = set()
        for cfg in self.best_configs:
            params.update((cfg.get("config") or {}).keys())
        params = sorted(params)

        for param in params:
            values = []
            for cfg in self.best_configs:
                v = self._safe_float((cfg.get("config") or {}).get(param))
                if v is None:
                    continue
                values.append((v, cfg))

            if not values:
                continue

            values_sorted = sorted(values, key=lambda t: t[0])
            min_v, min_cfg = values_sorted[0]
            max_v, max_cfg = values_sorted[-1]

            for mode, v, cfg in (("низкий", min_v, min_cfg), ("высокий", max_v, max_cfg)):
                m = cfg.get("metrics", {}) or {}
                d_tp, d_lat, d_err = self._compute_deltas_vs_baseline(m)
                row = (
                    param,
                    f"#{cfg.get('rank', '?')} ({mode})",
                    f"{v:g}",
                    self._format_delta_pct(d_tp),
                    self._format_delta_pct(d_lat),
                    self._format_delta_pct(d_err),
                    f"{m.get('fitness', 0):.4f}",
                )
                iid = self.param_tree.insert("", tk.END, values=row)
                self._param_row_map[iid] = {"param": param, "mode": mode, "config_data": cfg}

        self.analysis_text.insert(tk.END, "Выбери строку слева, чтобы увидеть подробности.\n\n")
        self.analysis_text.insert(
            tk.END,
            "Как читать Δ:\n"
            "  - Δ TP: изменение throughput относительно baseline.\n"
            "  - Δ Lat / Δ Err: плюс означает улучшение (т.к. latency/error меньше = лучше).\n\n"
            "Задача вкладки:\n"
            "  - Найти параметры, которые дают лучший эффект по нужной метрике,\n"
            "    и понять, что они ухудшают взамен.\n"
        )
    
    def update_evolution_graph(self):
        """Обновление графика эволюции с целыми числами на оси X"""
        if self.current_data is None:
            return
        
        for widget in self.evolution_frame.winfo_children():
            widget.destroy()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # График сходимости с целыми числами на оси X
        gen_stats = self.current_data.groupby('generation')['fitness'].agg(['mean', 'max', 'min']).reset_index()
        generations = gen_stats['generation'].astype(int).values
        
        ax1.plot(generations, gen_stats['max'], 'b-', linewidth=2, label='Max fitness', marker='o')
        ax1.plot(generations, gen_stats['mean'], 'g--', linewidth=2, label='Mean fitness', marker='s')
        ax1.fill_between(generations, gen_stats['min'], gen_stats['max'], alpha=0.2, color='blue')
        ax1.set_xticks(generations)
        ax1.set_xticklabels([int(x) for x in generations])
        ax1.set_xlabel('Поколение')
        ax1.set_ylabel('Fitness')
        ax1.set_title('Сходимость генетического алгоритма')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # График улучшения Throughput
        if 'throughput' in self.current_data.columns:
            tp_stats = self.current_data.groupby('generation')['throughput'].agg(['max', 'mean'])
            tp_generations = tp_stats.index.astype(int).values
            ax2.plot(tp_generations, tp_stats['max'], 'r-', linewidth=2, label='Max TPS', marker='o')
            ax2.plot(tp_generations, tp_stats['mean'], 'orange', linewidth=2, label='Mean TPS', marker='s')
            ax2.set_xticks(tp_generations)
            ax2.set_xticklabels([int(x) for x in tp_generations])
            ax2.set_xlabel('Поколение')
            ax2.set_ylabel('Throughput (TPS)')
            ax2.set_title('Улучшение пропускной способности')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # График снижения Latency
        if 'avg_latency' in self.current_data.columns:
            lat_stats = self.current_data.groupby('generation')['avg_latency'].agg(['min', 'mean'])
            lat_generations = lat_stats.index.astype(int).values
            ax3.plot(lat_generations, lat_stats['min'], 'purple', linewidth=2, label='Min latency', marker='o')
            ax3.plot(lat_generations, lat_stats['mean'], 'pink', linewidth=2, label='Mean latency', marker='s')
            ax3.set_xticks(lat_generations)
            ax3.set_xticklabels([int(x) for x in lat_generations])
            ax3.set_xlabel('Поколение')
            ax3.set_ylabel('Задержка (ms)')
            ax3.set_title('Снижение задержки')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # График эволюции параметров
        param_cols = [col for col in self.current_data.columns if col in 
                     ['shared_buffers', 'work_mem', 'random_page_cost']]
        
        for param in param_cols[:3]:
            if param in self.current_data.columns:
                param_stats = self.current_data.groupby('generation')[param].mean()
                param_generations = param_stats.index.astype(int).values
                ax4.plot(param_generations, param_stats.values, label=param, linewidth=2, marker='o')
        
        ax4.set_xticks(param_generations)
        ax4.set_xticklabels([int(x) for x in param_generations])
        ax4.set_xlabel('Поколение')
        ax4.set_ylabel('Значение параметра')
        ax4.set_title('Эволюция параметров (средние значения)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.evolution_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_status(self, message):
        """Обновление статус бара"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def export_report(self):
        """Экспорт отчета в HTML"""
        if not self.best_configs:
            messagebox.showwarning("Нет данных", "Нет данных для экспорта")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.results_dir / f"exported_report_{timestamp}.html"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("<!DOCTYPE html>\n")
                f.write("<html>\n<head>\n")
                f.write("<title>Report - PG Optimizer</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write("h1 { color: #2c3e50; }\n")
                f.write("h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }\n")
                f.write("table { border-collapse: collapse; width: 100%; margin: 10px 0; }\n")
                f.write("th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }\n")
                f.write("th { background-color: #3498db; color: white; }\n")
                f.write("tr:nth-child(even) { background-color: #f2f2f2; }\n")
                f.write(".good { color: green; font-weight: bold; }\n")
                f.write(".bad { color: red; font-weight: bold; }\n")
                f.write(".neutral { color: orange; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                
                f.write(f"<h1>Отчет об оптимизации PostgreSQL</h1>\n")
                f.write(f"<p><strong>Дата:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n\n")
                
                f.write("<h2>Лучшие найденные конфигурации</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Ранг</th><th>Fitness</th><th>Throughput (TPS)</th><th>Latency (ms)</th><th>Error Rate (%)</th></tr>\n")
                
                for config in self.best_configs:
                    metrics = config['metrics']
                    rank_display = "⭐ ВАЛИДАЦИЯ" if config.get('is_validation', False) else str(config['rank'])
                    f.write(f"<tr>")
                    f.write(f"<td>{rank_display}</td>")
                    f.write(f"<td>{metrics['fitness']:.4f}</td>")
                    f.write(f"<td>{metrics['throughput']:.2f}</td>")
                    f.write(f"<td>{metrics['avg_latency']:.2f}</td>")
                    f.write(f"<td>{metrics['error_rate']*100:.2f}%</td>")
                    f.write(f"</tr>\n")
                f.write("</table>\n\n")
                
                best = self.best_configs[0]
                f.write("<h2>Детали лучшей конфигурации</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Параметр</th><th>Значение</th></tr>\n")
                for param, value in best['config'].items():
                    f.write(f"<tr><td>{param}</td><td>{value}</td></tr>\n")
                f.write("</table>\n\n")
                
                if self.baseline_data:
                    f.write("<h2>Сравнение с базовой конфигурацией</h2>\n")
                    f.write("<table>\n")
                    f.write("<tr><th>Метрика</th><th>Baseline</th><th>Optimized</th><th>Изменение</th></tr>\n")
                    
                    baseline_tp = self.baseline_data.get('load_metrics', {}).get('throughput', 0)
                    best_tp = best['metrics']['throughput']
                    if baseline_tp > 0:
                        tp_change = ((best_tp - baseline_tp) / baseline_tp) * 100
                        tp_class = "good" if tp_change > 0 else "bad"
                        f.write(f"<tr><td>Throughput</td><td>{baseline_tp:.2f}</td><td>{best_tp:.2f}</td>")
                        f.write(f"<td class='{tp_class}'>{tp_change:+.1f}%</td></tr>\n")
                    
                    baseline_lat = self.baseline_data.get('load_metrics', {}).get('avg_latency', 0)
                    best_lat = best['metrics']['avg_latency']
                    if baseline_lat > 0:
                        lat_change = ((baseline_lat - best_lat) / baseline_lat) * 100
                        lat_class = "good" if lat_change > 0 else "bad"
                        f.write(f"<tr><td>Latency</td><td>{baseline_lat:.2f}</td><td>{best_lat:.2f}</td>")
                        f.write(f"<td class='{lat_class}'>{lat_change:+.1f}%</td></tr>\n")
                    
                    f.write("</table>\n")
                
                f.write("</body>\n</html>")
            
            messagebox.showinfo("Экспорт", f"Отчет сохранен в:\n{report_file}")
            self.update_status(f"Отчет экспортирован: {report_file.name}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчет: {e}")
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


def launch_viewer():
    """Запуск вьювера результатов"""
    viewer = ResultsViewer()
    viewer.run()


if __name__ == "__main__":
    launch_viewer()