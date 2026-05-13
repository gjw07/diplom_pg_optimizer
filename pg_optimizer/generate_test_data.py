#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для генерации тестовых данных в PostgreSQL.
Создает таблицы с реалистичными данными для нагрузочного тестирования.
Поддерживает три уровня сложности: simple, medium, complex.
"""

import psycopg2
import time
import logging
import argparse
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Класс для генерации тестовых данных в PostgreSQL."""
    
    def __init__(self, db_config: Dict[str, Any], schema_level: str = 'medium'):
        """
        Инициализация генератора.
        
        Args:
            db_config: Конфигурация подключения к БД
            schema_level: Уровень сложности ('simple', 'medium', 'complex')
        """
        self.db_config = db_config
        self.schema_level = schema_level
        self.conn = None
        self.cursor = None
        
        # Загружаем модуль схемы
        self.schema_module = self._load_schema_module()
        logger.info(f"TestDataGenerator инициализирован (схема: {schema_level})")
    
    def _load_schema_module(self):
        """Загружает модуль с выбранной схемой"""
        if self.schema_level == 'simple':
            from .schemas import simple_schema
            return simple_schema
        elif self.schema_level == 'complex':
            from .schemas import complex_schema
            return complex_schema
        else:
            from .schemas import medium_schema
            return medium_schema
    
    def connect(self) -> bool:
        """Устанавливает соединение с PostgreSQL"""
        try:
            # Используем правильные ключи из db_config
            port = self.db_config.get('PORT', 5432)
            user = self.db_config.get('POSTGRES_USER', 'test_user')
            password = self.db_config.get('POSTGRES_PASSWORD', 'test_password')
            database = self.db_config.get('POSTGRES_DB', 'test_db')
            
            logger.info(f"Подключение к БД: port={port}, user={user}, db={database}")
            
            self.conn = psycopg2.connect(
                host="localhost",
                port=port,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            logger.info("Соединение с PostgreSQL установлено")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return False
    
    def disconnect(self):
        """Закрывает соединение с PostgreSQL"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Соединение с PostgreSQL закрыто")
    
    def drop_all_tables(self):
        """Удаляет все таблицы в схеме public"""
        try:
            self.cursor.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
            self.conn.commit()
            logger.info("Все таблицы в схеме public удалены")
        except Exception as e:
            logger.error(f"Ошибка при удалении таблиц: {e}")
    
    def create_all_tables(self):
        """Создаёт таблицы через загруженный модуль схемы"""
        self.schema_module.create_tables(self.cursor)
        self.conn.commit()
        logger.info(f"Таблицы схемы '{self.schema_level}' созданы")
    
    def generate_full_dataset(self, counts: dict = None):
        """Генерирует данные через загруженный модуль схемы"""
        if counts is None:
            # Значения по умолчанию
            counts = {
                'employees': 200,
                'customers': 500,
                'products': 50,
                'orders': 1000
            }
        
        logger.info(f"Генерация данных для схемы '{self.schema_level}'...")
        start_time = time.time()
        
        self.schema_module.generate_data(self.cursor, counts)
        self.conn.commit()
        
        elapsed = time.time() - start_time
        logger.info(f"Генерация данных завершена за {elapsed:.2f} сек")
        
        # Вывод статистики
        self._print_stats()
        
        return True
    
    def _print_stats(self):
        """Выводит статистику по таблицам"""
        try:
            tables = ['test_employees', 'test_customers', 'test_products', 
                      'test_orders', 'test_order_details']
            stats = {}
            for table in tables:
                try:
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = self.cursor.fetchone()[0]
                except:
                    pass
            
            logger.info("=" * 50)
            logger.info("Статистика таблиц:")
            for table, count in stats.items():
                logger.info(f"  {table}: {count:,} записей")
            logger.info("=" * 50)
        except Exception as e:
            logger.warning(f"Не удалось получить статистику: {e}")


def main():
    """Точка входа для самостоятельного запуска генератора"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    parser = argparse.ArgumentParser(description='Генерация тестовых данных для PostgreSQL')
    parser.add_argument('--schema', '-s', choices=['simple', 'medium', 'complex'], 
                        default='medium', help='Тип схемы БД')
    
    args = parser.parse_args()
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    db_config = {
        'POSTGRES_PORT': 5432,
        'POSTGRES_USER': 'test_user',
        'POSTGRES_PASSWORD': 'test_password',
        'POSTGRES_DB': 'test_db'
    }
    
    generator = TestDataGenerator(db_config, schema_level=args.schema)
    
    if generator.connect():
        generator.drop_all_tables()
        generator.create_all_tables()
        generator.generate_full_dataset()
        generator.disconnect()
        print(f"\n✅ Генерация тестовых данных (схема: {args.schema}) завершена успешно!")
    else:
        print("❌ Не удалось подключиться к PostgreSQL")


if __name__ == "__main__":
    main()