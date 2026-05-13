#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль со сложными запросами для нагрузочного тестирования PostgreSQL.
Содержит различные типы запросов: от простых до сложных аналитических.
"""

import random
from typing import List, Dict, Any


class TestQueries:
    """
    Класс, содержащий набор запросов для нагрузочного тестирования.
    Запросы разбиты по уровням сложности.
    """
    
    # ================================================================
    # ПРОСТЫЕ ЗАПРОСЫ (уровень 1)
    # ================================================================
    
    SIMPLE_QUERIES = [
        # Поиск сотрудника по ID
        "SELECT * FROM test_employees WHERE employee_id = 'EMP000001';",
        
        # Поиск заказа по номеру
        "SELECT * FROM test_orders WHERE order_number = 'ORD000000001';",
        
        # Подсчет количества сотрудников в отделе
        "SELECT department, COUNT(*) FROM test_employees GROUP BY department;",
        
        # Поиск продукта по категории
        "SELECT * FROM test_products WHERE category = 'Электроника' LIMIT 10;",
        
        # Проверка существования клиента
        "SELECT COUNT(*) FROM test_customers WHERE city = 'Москва';",
    ]
    
    # ================================================================
    # СРЕДНИЕ ЗАПРОСЫ (уровень 2) - JOIN 2-3 таблиц
    # ================================================================
    
    MEDIUM_QUERIES = [
        # Заказы с информацией о клиентах
        """
        SELECT o.order_number, o.order_date, o.total_amount, 
               c.first_name, c.last_name, c.city
        FROM test_orders o
        JOIN test_customers c ON o.customer_id = c.id
        WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
        LIMIT 100;
        """,
        
        # Заказы с информацией о сотрудниках
        """
        SELECT o.order_number, o.total_amount, 
               e.first_name, e.last_name, e.department
        FROM test_orders o
        JOIN test_employees e ON o.employee_id = e.id
        WHERE o.status = 'completed'
        LIMIT 100;
        """,
        
        # Детали заказа с информацией о продуктах
        """
        SELECT od.order_id, p.name, od.quantity, od.unit_price, 
               od.quantity * od.unit_price as total
        FROM test_order_details od
        JOIN test_products p ON od.product_id = p.id
        WHERE od.order_id = 1000;
        """,
        
        # Активные сотрудники с их заказами (агрегация)
        """
        SELECT e.first_name, e.last_name, e.department, 
               COUNT(o.id) as order_count,
               COALESCE(SUM(o.total_amount), 0) as total_sales
        FROM test_employees e
        LEFT JOIN test_orders o ON e.id = o.employee_id AND o.status = 'completed'
        WHERE e.is_active = true
        GROUP BY e.id, e.first_name, e.last_name, e.department
        ORDER BY total_sales DESC
        LIMIT 50;
        """,
        
        # Продажи по категориям
        """
        SELECT p.category, 
               COUNT(DISTINCT od.order_id) as order_count,
               SUM(od.quantity) as items_sold,
               SUM(od.quantity * od.unit_price) as revenue
        FROM test_products p
        JOIN test_order_details od ON p.id = od.product_id
        JOIN test_orders o ON od.order_id = o.id
        WHERE o.status = 'completed'
        GROUP BY p.category
        ORDER BY revenue DESC;
        """,
    ]
    
    # ================================================================
    # СЛОЖНЫЕ ЗАПРОСЫ (уровень 3) - множественные JOIN, подзапросы, оконные функции
    # ================================================================
    
    COMPLEX_QUERIES = [
        # Топ-10 клиентов по сумме заказов с оконной функцией
        """
        WITH customer_totals AS (
            SELECT c.id, c.first_name, c.last_name, c.city,
                   SUM(o.total_amount) as total_spent,
                   COUNT(o.id) as order_count,
                   ROW_NUMBER() OVER (ORDER BY SUM(o.total_amount) DESC) as rank
            FROM test_customers c
            JOIN test_orders o ON c.id = o.customer_id
            WHERE o.status = 'completed'
            GROUP BY c.id, c.first_name, c.last_name, c.city
        )
        SELECT first_name, last_name, city, total_spent, order_count, rank
        FROM customer_totals
        WHERE rank <= 10
        ORDER BY rank;
        """,
        
        # Ежемесячный отчет по продажам с накопительным итогом
        """
        WITH monthly_sales AS (
            SELECT 
                DATE_TRUNC('month', order_date) as month,
                SUM(total_amount) as monthly_revenue,
                COUNT(*) as order_count
            FROM test_orders
            WHERE status = 'completed'
            GROUP BY DATE_TRUNC('month', order_date)
        )
        SELECT 
            TO_CHAR(month, 'YYYY-MM') as month,
            monthly_revenue,
            order_count,
            SUM(monthly_revenue) OVER (ORDER BY month) as cumulative_revenue
        FROM monthly_sales
        ORDER BY month DESC
        LIMIT 12;
        """,
        
        # Анализ эффективности сотрудников (средний чек, количество заказов)
        """
        SELECT 
            e.first_name || ' ' || e.last_name as employee_name,
            e.department,
            COUNT(o.id) as orders_processed,
            AVG(o.total_amount) as avg_order_value,
            SUM(o.total_amount) as total_revenue,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY o.total_amount) as median_order_value
        FROM test_employees e
        JOIN test_orders o ON e.id = o.employee_id
        WHERE o.status = 'completed'
        GROUP BY e.id, e.first_name, e.last_name, e.department
        HAVING COUNT(o.id) > 10
        ORDER BY total_revenue DESC
        LIMIT 20;
        """,
        
        # Корреляция между опытом сотрудника и объемом продаж
        """
        SELECT 
            e.department,
            EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)) as years_of_service,
            COUNT(o.id) as orders_count,
            AVG(o.total_amount) as avg_order_value,
            SUM(o.total_amount) as total_revenue
        FROM test_employees e
        JOIN test_orders o ON e.id = o.employee_id
        WHERE o.status = 'completed' AND e.hire_date IS NOT NULL
        GROUP BY e.department, EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date))
        ORDER BY e.department, years_of_service;
        """,
        
        # Анализ повторных покупок (RFM-анализ)
        """
        WITH customer_orders AS (
            SELECT 
                c.id,
                c.first_name || ' ' || c.last_name as customer_name,
                COUNT(o.id) as frequency,
                SUM(o.total_amount) as monetary,
                MAX(o.order_date) as last_order_date
            FROM test_customers c
            JOIN test_orders o ON c.id = o.customer_id
            WHERE o.status = 'completed'
            GROUP BY c.id
        ),
        rfm_scores AS (
            SELECT 
                id,
                customer_name,
                frequency,
                monetary,
                NTILE(4) OVER (ORDER BY frequency DESC) as frequency_score,
                NTILE(4) OVER (ORDER BY monetary DESC) as monetary_score,
                NTILE(4) OVER (ORDER BY last_order_date DESC) as recency_score
            FROM customer_orders
        )
        SELECT 
            customer_name,
            frequency,
            monetary,
            (frequency_score + monetary_score + recency_score) as rfm_score,
            CASE 
                WHEN (frequency_score + monetary_score + recency_score) >= 10 THEN 'VIP'
                WHEN (frequency_score + monetary_score + recency_score) >= 7 THEN 'Loyal'
                WHEN (frequency_score + monetary_score + recency_score) >= 4 THEN 'Regular'
                ELSE 'At Risk'
            END as customer_segment
        FROM rfm_scores
        ORDER BY rfm_score DESC
        LIMIT 50;
        """,
    ]
    
    # ================================================================
    # ОЧЕНЬ СЛОЖНЫЕ ЗАПРОСЫ (уровень 4) - рекурсивные CTE, множественные подзапросы
    # ================================================================
    
    VERY_COMPLEX_QUERIES = [
        # Иерархия продуктов и категорий (рекурсивный CTE)
        """
        WITH ranked_employees AS (
            SELECT 
                department,
                first_name,
                last_name,
                salary,
                ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank
            FROM test_employees
        )
        SELECT department, first_name, last_name, salary
        FROM ranked_employees
        WHERE rank <= 3
        ORDER BY department, rank
        """,
 
    ]
    
    # ================================================================
    # ЗАПРОСЫ ДЛЯ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ (с параметрами)
    # ================================================================
    
    @classmethod
    def get_random_simple_query(cls) -> str:
        """Возвращает случайный простой запрос"""
        return random.choice(cls.SIMPLE_QUERIES)
    
    @classmethod
    def get_random_medium_query(cls) -> str:
        """Возвращает случайный средний запрос"""
        return random.choice(cls.MEDIUM_QUERIES)
    
    @classmethod
    def get_random_complex_query(cls) -> str:
        """Возвращает случайный сложный запрос"""
        return random.choice(cls.COMPLEX_QUERIES)
    
    @classmethod
    def get_random_very_complex_query(cls) -> str:
        """Возвращает случайный очень сложный запрос"""
        return random.choice(cls.VERY_COMPLEX_QUERIES)
    
    @classmethod
    def get_parameterized_query(cls, query_type: str = 'mixed') -> str:
        """
        Возвращает параметризованный запрос для нагрузочного тестирования.
        
        Args:
            query_type: 'simple', 'medium', 'complex', 'very_complex', 'mixed'
        
        Returns:
            str: SQL-запрос
        """
        if query_type == 'simple':
            return cls.get_random_simple_query()
        elif query_type == 'medium':
            return cls.get_random_medium_query()
        elif query_type == 'complex':
            return cls.get_random_complex_query()
        elif query_type == 'very_complex':
            return cls.get_random_very_complex_query()
        else:  # mixed
            weights = [0.3, 0.4, 0.2, 0.1]  # 30% простых, 40% средних, 20% сложных, 10% очень сложных
            query_classes = [cls.SIMPLE_QUERIES, cls.MEDIUM_QUERIES, 
                           cls.COMPLEX_QUERIES, cls.VERY_COMPLEX_QUERIES]
            chosen_class = random.choices(query_classes, weights=weights)[0]
            return random.choice(chosen_class)
    
    @classmethod
    def get_all_queries(cls) -> Dict[str, List[str]]:
        """Возвращает все запросы по категориям"""
        return {
            'simple': cls.SIMPLE_QUERIES,
            'medium': cls.MEDIUM_QUERIES,
            'complex': cls.COMPLEX_QUERIES,
            'very_complex': cls.VERY_COMPLEX_QUERIES
        }
    
    @classmethod
    def get_query_summary(cls) -> Dict[str, int]:
        """Возвращает количество запросов по категориям"""
        return {
            'simple': len(cls.SIMPLE_QUERIES),
            'medium': len(cls.MEDIUM_QUERIES),
            'complex': len(cls.COMPLEX_QUERIES),
            'very_complex': len(cls.VERY_COMPLEX_QUERIES),
            'total': len(cls.SIMPLE_QUERIES) + len(cls.MEDIUM_QUERIES) + \
                     len(cls.COMPLEX_QUERIES) + len(cls.VERY_COMPLEX_QUERIES)
        }


# ================================================================
# Функции для интеграции с существующим кодом
# ================================================================

def get_mixed_workload_queries(num_queries: int = 100) -> List[str]:
    """
    Генерирует список запросов для смешанной рабочей нагрузки.
    
    Args:
        num_queries: Количество запросов
    
    Returns:
        List[str]: Список SQL-запросов
    """
    queries = []
    for _ in range(num_queries):
        queries.append(TestQueries.get_parameterized_query('mixed'))
    return queries


def get_workload_profile(profile: str = 'oltp') -> List[str]:
    """
    Возвращает профиль нагрузки.
    
    Args:
        profile: 'oltp' (много простых), 'olap' (много сложных), 'mixed' (смешанная)
    
    Returns:
        List[str]: Список SQL-запросов
    """
    if profile == 'oltp':
        return TestQueries.SIMPLE_QUERIES * 5
    elif profile == 'olap':
        return TestQueries.COMPLEX_QUERIES + TestQueries.VERY_COMPLEX_QUERIES
    else:  # mixed
        return TestQueries.SIMPLE_QUERIES + TestQueries.MEDIUM_QUERIES + \
               TestQueries.COMPLEX_QUERIES + TestQueries.VERY_COMPLEX_QUERIES


if __name__ == "__main__":
    print("=" * 60)
    print("Тестовые запросы PG Optimizer")
    print("=" * 60)
    
    summary = TestQueries.get_query_summary()
    print(f"\nВсего запросов: {summary['total']}")
    print(f"  - Простые: {summary['simple']}")
    print(f"  - Средние: {summary['medium']}")
    print(f"  - Сложные: {summary['complex']}")
    print(f"  - Очень сложные: {summary['very_complex']}")
    
    print("\nПримеры запросов:")
    
    print("\n[ПРОСТОЙ]")
    print(TestQueries.get_random_simple_query())
    
    print("\n[СРЕДНИЙ]")
    print(TestQueries.get_random_medium_query())
    
    print("\n[СЛОЖНЫЙ]")
    print(TestQueries.get_random_complex_query())
    
    print("\n[ОЧЕНЬ СЛОЖНЫЙ]")
    print(TestQueries.get_random_very_complex_query())