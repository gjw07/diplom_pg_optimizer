import subprocess
import csv
import os
import time
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)


class LoadTester:
    """
    Класс для проведения нагрузочного тестирования с помощью JMeter.
    Соответствует модулю load_generator из архитектурного плана.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация нагрузочного тестера.
        
        Args:
            config: Конфигурация JMeter из config.py
        """
        self.config = config
        self._create_test_plan()
        logger.info("LoadTester инициализирован")
    
    def _create_test_plan(self):
        """
        Создает JMeter тест-план программно.
        В реальном проекте лучше использовать готовый .jmx файл.
        """
        # Создаем простой тест-план для демонстрации
        jmx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="PostgreSQL Test Plan">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Database Thread Group">
        <intProp name="ThreadGroup.num_threads">{self.config['NUM_THREADS']}</intProp>
        <intProp name="ThreadGroup.ramp_time">{self.config['RAMP_UP']}</intProp>
        <longProp name="ThreadGroup.duration">{self.config['TEST_DURATION']}</longProp>
      </ThreadGroup>
      <hashTree>
        <JDBCDataSource guiclass="TestBeanGUI" testclass="JDBCDataSource" testname="PostgreSQL Connection">
          <stringProp name="databaseUrl">jdbc:postgresql://localhost:5432/test_db</stringProp>
          <stringProp name="username">test_user</stringProp>
          <stringProp name="password">test_password</stringProp>
        </JDBCDataSource>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''
        
        with open('test_plan.jmx', 'w') as f:
            f.write(jmx_content)
    
    def run_test(self, test_name: str = "test") -> str:
        """
        Запускает нагрузочный тест.
        
        Args:
            test_name: Имя теста для идентификации результатов
            
        Returns:
            str: Путь к файлу с результатами
        """
        try:
            # Создаем директорию для результатов
            os.makedirs(self.config['RESULTS_DIR'], exist_ok=True)
            
            # Формируем имена выходных файлов
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            results_file = f"{self.config['RESULTS_DIR']}{test_name}_{timestamp}.jtl"
            log_file = f"{self.config['RESULTS_DIR']}{test_name}_{timestamp}.log"
            
            # Формируем команду JMeter
            cmd = [
                self.config['JMETER_PATH'],
                '-n',  # non-gui mode
                '-t', self.config['TEST_PLAN'],
                '-l', results_file,
                '-j', log_file
            ]
            
            logger.info(f"Запуск JMeter: {' '.join(cmd)}")
            
            # Запускаем JMeter
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем завершения теста
            stdout, stderr = process.communicate(timeout=self.config['TEST_DURATION'] + 30)
            
            if process.returncode == 0:
                logger.info(f"Тест завершен успешно. Результаты: {results_file}")
                return results_file
            else:
                logger.error(f"Ошибка JMeter: {stderr}")
                return ""
                
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при выполнении теста")
            process.kill()
            return ""
        except Exception as e:
            logger.error(f"Ошибка при запуске теста: {e}")
            return ""
    
    def parse_results(self, results_file: str) -> Dict[str, float]:
        """
        Парсит результаты нагрузочного тестирования.
        
        Args:
            results_file: Путь к JTL файлу с результатами
            
        Returns:
            Dict: Словарь с метриками производительности
        """
        metrics = {
            'throughput': 0.0,      # пропускная способность (TPS)
            'avg_latency': 0.0,      # средняя задержка (ms)
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
            
            # Читаем JTL файл (CSV формат)
            df = pd.read_csv(results_file, sep=',', comment='#', 
                           names=['timestamp', 'elapsed', 'responseCode', 
                                 'responseMessage', 'threadName', 'success'])
            
            if len(df) > 0:
                # Пропускная способность (запросов в секунду)
                test_duration = (df['timestamp'].max() - df['timestamp'].min()) / 1000
                if test_duration > 0:
                    metrics['throughput'] = len(df) / test_duration
                
                # Задержки
                metrics['avg_latency'] = df['elapsed'].mean()
                metrics['min_latency'] = df['elapsed'].min()
                metrics['max_latency'] = df['elapsed'].max()
                
                # Успешные запросы
                metrics['total_requests'] = len(df)
                metrics['successful_requests'] = df['success'].sum()
                metrics['error_rate'] = 1 - (metrics['successful_requests'] / metrics['total_requests'])
            
            logger.info(f"Результаты теста: Throughput={metrics['throughput']:.2f} TPS, "
                       f"Avg Latency={metrics['avg_latency']:.2f} ms")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге результатов: {e}")
        
        return metrics