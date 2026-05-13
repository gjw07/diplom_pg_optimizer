"""
Конфигурационный файл проекта.
Содержит все настраиваемые параметры системы.
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Параметры оптимизируемых генов (параметров PostgreSQL)
# Формат: "имя_параметра": {
#     'min': минимальное значение,
#     'max': максимальное значение,
#     'type': тип данных (int/float),
#     'unit': единица измерения,
#     'description': описание параметра
# }
OPTIMIZABLE_PARAMS = {
    'shared_buffers': {
        'min': 128,      # MB
        'max': 4096,     # MB (4GB)
        'type': int,
        'unit': 'MB',
        'description': 'Объем памяти для кэширования данных'
    },
    'work_mem': {
        'min': 4,        # MB
        'max': 256,      # MB
        'type': int,
        'unit': 'MB',
        'description': 'Память для операций сортировки и хеширования'
    },
    'maintenance_work_mem': {
        'min': 64,       # MB
        'max': 1024,     # MB (1GB)
        'type': int,
        'unit': 'MB',
        'description': 'Память для операций техобслуживания'
    },
    'random_page_cost': {
        'min': 1.0,
        'max': 4.0,
        'type': float,
        'unit': '',
        'description': 'Стоимость случайного доступа к диску'
    },
    'effective_cache_size': {
        'min': 1024,     # MB (1GB)
        'max': 16384,    # MB (16GB)
        'type': int,
        'unit': 'MB',
        'description': 'Оценка объема памяти для кэширования ОС'
    },
    'checkpoint_timeout': {
        'min': 30,       # seconds
        'max': 900,      # seconds (15 min)
        'type': int,
        'unit': 'sec',
        'description': 'Частота выполнения контрольных точек'
    }
}

# Параметры генетического алгоритма
GA_CONFIG = {
    'POPULATION_SIZE': 10,   # было 3
    'GENERATIONS': 5,       # было 3
    'CXPB': 0.7,
    'MUTPB': 0.2,
    'TOURNSIZE': 3,
}

# Параметры Docker
DOCKER_CONFIG = {
    'IMAGE_NAME': 'postgres:14',
    'CONTAINER_NAME': 'pg_optimization_test',
    'PORT': 5432,
    'POSTGRES_USER': 'test_user',
    'POSTGRES_PASSWORD': 'test_password',
    'POSTGRES_DB': 'test_db',
    'CONFIG_PATH': '/var/lib/postgresql/data/postgresql.conf'
}

# Параметры нагрузочного тестирования
JMETER_CONFIG = {
    'JMETER_PATH': 'D:/Program Files/apache-jmeter-5.6.3/bin/jmeter.bat',  # или полный путь к jmeter.bat
    'TEST_PLAN': os.path.join(PROJECT_ROOT, 'test_plan.jmx'),  # ПОЛНЫЙ ПУТЬ!
    'RESULTS_DIR': os.path.join(PROJECT_ROOT, 'results/'),
    'TEST_DURATION': 30,       # seconds
    'NUM_THREADS': 10,         # количество виртуальных пользователей
    'RAMP_UP': 5,              # время наращивания нагрузки (сек)
    'USE_WORKLOAD_GENERATOR': True,  # <-- НОВЫЙ ПАРАМЕТР: использовать генератор сложных запросов
    'WORKLOAD_PARALLEL': 4,          # <-- Количество параллельных потоков
    'WORKLOAD_QUERY_MIX': 'mixed',   # <-- Тип нагрузки: 'oltp', 'olap', 'mixed'
}
# Параметры фитнес-функции
FITNESS_CONFIG = {
    'TARGET_TP': 150,         # Целевая пропускная способность (TPS)
    'MAX_LATENCY': 100,        # Максимально допустимая задержка (ms)
    'CPU_WEIGHT': 0.2,         # Вес CPU в фитнес-функции
    'IO_WEIGHT': 0.1,          # Вес I/O в фитнес-функции
    'LATENCY_WEIGHT': 0.3,     # Вес задержки
    'TP_WEIGHT': 0.4           # Вес пропускной способности
}

# Параметры путей
PATHS = {
    'RESULTS_DIR': './experiment_results/',
    'LOGS_DIR': './logs/',
    'CONFIGS_DIR': './configs/',
    'PLOTS_DIR': './plots/'
}

# Настройка схемы базы данных
DATABASE_SCHEMA = {
    # Уровень схемы: 'simple', 'medium', 'complex'
    'LEVEL': 'simple',  # <-- МЕНЯЙТЕ ЗДЕСЬ для выбора схемы
    
    # Объём данных: 'small', 'medium', 'large'
    'DATA_SIZE': 'small',  # <-- МЕНЯЙТЕ ЗДЕСЬ для выбора объёма
    
    # Доступные схемы
    'SCHEMAS': {
        'simple': {
            'name': 'Простая схема',
            'description': '2 таблицы: employees, departments'
        },
        'medium': {
            'name': 'Средняя схема',
            'description': '4 таблицы: employees, departments, projects, employee_projects'
        },
        'complex': {
            'name': 'Сложная схема',
            'description': '8+ таблиц: иерархия отделов, навыки, история зарплат'
        }
    },
    
    # Объёмы данных для каждой схемы
    'DATA_VOLUMES': {
        'small': {
            'name': 'Маленький',
            'employees': 50,
            'customers': 100,
            'products': 20,
            'orders': 200,
            'projects': 10,
            'skills': 15
        },
        'medium': {
            'name': 'Средний',
            'employees': 200,
            'customers': 500,
            'products': 50,
            'orders': 1000,
            'projects': 20,
            'skills': 25
        },
        'large': {
            'name': 'Большой',
            'employees': 1000,
            'customers': 5000,
            'products': 200,
            'orders': 10000,
            'projects': 50,
            'skills': 40
        }
    }
}
