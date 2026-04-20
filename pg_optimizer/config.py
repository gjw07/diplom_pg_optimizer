"""
Конфигурационный файл проекта.
Содержит все настраиваемые параметры системы.
"""

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
    'POPULATION_SIZE': 10,      # Размер популяции
    'GENERATIONS': 5,           # Количество поколений
    'CXPB': 0.7,                # Вероятность скрещивания (crossover probability)
    'MUTPB': 0.2,               # Вероятность мутации (mutation probability)
    'TOURNSIZE': 3,             # Размер турнира для отбора
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
    'JMETER_PATH': 'jmeter',  # или полный путь к jmeter.bat
    'TEST_PLAN': 'test_plan.jmx',
    'RESULTS_DIR': './results/',
    'TEST_DURATION': 30,       # seconds
    'NUM_THREADS': 10,         # количество виртуальных пользователей
    'RAMP_UP': 5               # время наращивания нагрузки (сек)
}

# Параметры фитнес-функции
FITNESS_CONFIG = {
    'TARGET_TP': 1000,         # Целевая пропускная способность (TPS)
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
