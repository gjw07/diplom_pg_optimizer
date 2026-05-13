import docker
import time
import os
import logging
from typing import Dict, Any
import subprocess

from . import config 

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBController:
    """
    Класс для управления экземпляром PostgreSQL в Docker контейнере.
    Соответствует модулю db_controller из архитектурного плана.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация контроллера БД.
        
        Args:
            config: Словарь с конфигурацией Docker из config.py
        """
        self.config = config
        self.client = docker.from_env()
        self.container = None
        logger.info("DBController инициализирован")
    
    def start_container(self) -> bool:
        """
        Запускает Docker контейнер с PostgreSQL.
        
        Returns:
            bool: True если контейнер успешно запущен, иначе False
        """
        try:
            # Проверяем, не запущен ли уже контейнер
            try:
                self.container = self.client.containers.get(self.config['CONTAINER_NAME'])
                logger.info(f"Контейнер {self.config['CONTAINER_NAME']} уже существует")
                if self.container.status != 'running':
                    self.container.start()
                    logger.info("Контейнер запущен")
                return True
            except docker.errors.NotFound:
                # Контейнер не найден, создаем новый
                logger.info(f"Создание нового контейнера {self.config['CONTAINER_NAME']}")
                
                # Создаем временную директорию для конфигурации
                os.makedirs('./postgres_config', exist_ok=True)
                
                self.container = self.client.containers.run(
                    self.config['IMAGE_NAME'],
                    name=self.config['CONTAINER_NAME'],
                    environment={
                        'POSTGRES_USER': self.config['POSTGRES_USER'],
                        'POSTGRES_PASSWORD': self.config['POSTGRES_PASSWORD'],
                        'POSTGRES_DB': self.config['POSTGRES_DB'],
                        'POSTGRES_MAX_CONNECTIONS': '200' 
                    },
                    ports={'5432/tcp': self.config['PORT']},
                    volumes={
                        os.path.abspath('./postgres_config'): {
                            'bind': '/docker-entrypoint-initdb.d/',
                            'mode': 'rw'
                        }
                    },
                    detach=True,
                    remove=True
                )
                logger.info("Контейнер успешно создан и запущен")
                
                # Ждем, пока PostgreSQL полностью загрузится
                time.sleep(10)
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при запуске контейнера: {e}")
            return False
    
    def stop_container(self) -> bool:
        """
        Останавливает Docker контейнер.
        
        Returns:
            bool: True если контейнер успешно остановлен
        """
        try:
            if self.container:
                self.container.stop()
                logger.info("Контейнер остановлен")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при остановке контейнера: {e}")
            return False
    
    def apply_config(self, params: Dict[str, Any]) -> bool:
        """Применяет новую конфигурацию к PostgreSQL."""
        try:
            # Используем абсолютный путь
            config_dir = os.path.join(config.PROJECT_ROOT, 'postgres_config')
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, 'custom.conf')
            
            # Формируем строки конфигурации
            config_lines = []
            for key, value in params.items():
                if key in ['shared_buffers', 'work_mem', 'maintenance_work_mem', 'effective_cache_size']:
                    config_lines.append(f"{key} = '{value}MB'")
                elif key == 'random_page_cost':
                    config_lines.append(f"{key} = {value}")
                elif key == 'checkpoint_timeout':
                    config_lines.append(f"{key} = '{value}s'")
                else:
                    config_lines.append(f"{key} = {value}")
            
            # Создаем файл с конфигурацией
            config_content = '\n'.join(config_lines)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # Копируем файл в контейнер
            if self.container:
                # Читаем содержимое файла
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Создаем файл в контейнере
                self.container.exec_run(
                    f'bash -c "echo \'{content}\' > /tmp/custom.conf"'
                )
                
                # Добавляем include в основной конфиг (если еще не добавлено)
                self.container.exec_run(
                    'bash -c "grep -q \'include_if_exists = \'/tmp/custom.conf\'\' /var/lib/postgresql/data/postgresql.conf || echo \'include_if_exists = \'/tmp/custom.conf\'\' >> /var/lib/postgresql/data/postgresql.conf"'
                )
                
                logger.info(f"Конфигурация применена: {params}")
                return True
            else:
                logger.error("Контейнер не запущен")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при применении конфигурации: {e}")
            return False

    
    def restart_db(self) -> bool:
        """
        Перезапускает PostgreSQL для применения новой конфигурации.
        
        Returns:
            bool: True если перезапуск успешен
        """
        try:
            if self.container:
                self.container.exec_run('pg_ctl reload')
                logger.info("PostgreSQL перезапущен")
                time.sleep(3)  # Даем время на перезапуск
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при перезапуске PostgreSQL: {e}")
            return False
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Получает текущую конфигурацию PostgreSQL.
        
        Returns:
            Dict: Словарь с текущими параметрами конфигурации
        """
        config = {}
        try:
            if self.container:
                # Выполняем SQL запрос для получения параметров
                result = self.container.exec_run(
                    f'psql -U {self.config["POSTGRES_USER"]} -d {self.config["POSTGRES_DB"]} -c "SHOW ALL;"'
                )
                
                # Парсим результат (упрощенно)
                output = result.output.decode('utf-8')
                logger.info("Текущая конфигурация получена")
                
                # TODO: Добавить парсинг вывода psql
                
        except Exception as e:
            logger.error(f"Ошибка при получении конфигурации: {e}")
        
        return config
    
    def get_container_stats(self) -> Dict[str, float]:
        """
        Получает статистику использования ресурсов контейнером.
        
        Returns:
            Dict: Статистика CPU и памяти
        """
        stats = {'cpu_usage': 0.0, 'memory_usage': 0.0}
        try:
            if self.container:
                container_stats = self.container.stats(stream=False)
                
                # Расчет CPU usage (упрощенно)
                cpu_delta = container_stats['cpu_stats']['cpu_usage']['total_usage'] - \
                            container_stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = container_stats['cpu_stats']['system_cpu_usage'] - \
                               container_stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    stats['cpu_usage'] = (cpu_delta / system_delta) * 100.0
                
                # Memory usage
                stats['memory_usage'] = container_stats['memory_stats']['usage'] / \
                                         container_stats['memory_stats']['limit'] * 100.0
                
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
        
        return stats