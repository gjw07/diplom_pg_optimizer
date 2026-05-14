#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Простая схема базы данных (2 таблицы)"""

import random
from datetime import datetime, timedelta


def create_tables(cursor):
    """Создаёт простые таблицы"""
    
    cursor.execute("""
        DROP TABLE IF EXISTS employees CASCADE;
        DROP TABLE IF EXISTS departments CASCADE;
    """)
    
    cursor.execute("""
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            dept_code VARCHAR(10) NOT NULL UNIQUE,
            dept_name VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            budget NUMERIC(12,2),
            head_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE employees (
            id SERIAL PRIMARY KEY,
            emp_id VARCHAR(20) NOT NULL UNIQUE,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            department_id INTEGER REFERENCES departments(id),
            position VARCHAR(50),
            salary NUMERIC(10,2),
            hire_date DATE,
            birth_date DATE,
            email VARCHAR(100),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX idx_emp_dept ON employees(department_id);")
    cursor.execute("CREATE INDEX idx_emp_salary ON employees(salary);")
    cursor.execute("CREATE INDEX idx_emp_hire_date ON employees(hire_date);")
    
    print("✅ Простая схема создана (2 таблицы)")


def generate_data(cursor, counts: dict):
    """Генерирует тестовые данные"""
    
    departments = [
        ('IT', 'Information Technology', 'Moscow', 2000000, 0),
        ('HR', 'Human Resources', 'Moscow', 500000, 0),
        ('SALES', 'Sales', 'Saint Petersburg', 800000, 0),
        ('FIN', 'Finance', 'Moscow', 600000, 0),
        ('OPS', 'Operations', 'Kazan', 700000, 0),
        ('RND', 'Research & Development', 'Novosibirsk', 1500000, 0),
        ('LEGAL', 'Legal', 'Moscow', 400000, 0),
        ('PR', 'Public Relations', 'Moscow', 300000, 0),
    ]
    
    for dept in departments:
        cursor.execute("""
            INSERT INTO departments (dept_code, dept_name, location, budget, head_count)
            VALUES (%s, %s, %s, %s, %s)
        """, dept)
    
    first_names = ['Иван', 'Петр', 'Анна', 'Мария', 'Алексей', 'Елена', 'Дмитрий', 'Ольга',
                   'Сергей', 'Татьяна', 'Андрей', 'Наталья', 'Владимир', 'Екатерина', 'Павел', 'Юлия']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецова', 'Смирнов', 'Волкова',
                  'Морозов', 'Новикова', 'Козлов', 'Лебедева', 'Соколов', 'Михайлова']
    positions = ['Junior', 'Middle', 'Senior', 'Team Lead', 'Manager', 'Director']
    
    employee_count = counts.get('employees', 2000)
    start_date = datetime.now() - timedelta(days=3650)
    
    for i in range(employee_count):
        emp_id = f"EMP{str(i+1).zfill(6)}"
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        dept_id = (i % 8) + 1
        position = positions[i % len(positions)]
        salary = 30000 + random.randint(0, 170000)
        hire_date = start_date + timedelta(days=random.randint(0, 3650))
        birth_date = start_date - timedelta(days=random.randint(7000, 15000))
        email = f"{first.lower()}.{last.lower()}@company.com"
        phone = f"+7{random.randint(9000000000, 9999999999)}"
        is_active = random.random() > 0.1
        
        cursor.execute("""
            INSERT INTO employees 
            (emp_id, first_name, last_name, department_id, position, salary, hire_date, birth_date, email, phone, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (emp_id, first, last, dept_id, position, salary, hire_date, birth_date, email, phone, is_active))
        
        if (i + 1) % 500 == 0:
            cursor.connection.commit()
            print(f"  Загружено {i+1} сотрудников...")
    
    # Обновляем head_count в отделах
    cursor.execute("""
        UPDATE departments d SET head_count = (
            SELECT COUNT(*) FROM employees e WHERE e.department_id = d.id
        )
    """)
    
    cursor.connection.commit()
    print(f"✅ Создано {employee_count} сотрудников")


def get_test_queries():
    """Возвращает запросы для тестирования схемы SIMPLE"""
    return {
        'simple': [
            "SELECT 1",
            "SELECT COUNT(*) FROM employees",
            "SELECT COUNT(*) FROM departments",
            "SELECT * FROM employees LIMIT 10",
            "SELECT * FROM departments LIMIT 5",
        ],
        'medium': [
            # Простые JOIN
            """
            SELECT e.first_name, e.last_name, d.dept_name, e.salary
            FROM employees e 
            JOIN departments d ON e.department_id = d.id 
            WHERE e.salary > 50000
            LIMIT 100
            """,
            """
            SELECT d.dept_name, COUNT(e.id) as emp_count, AVG(e.salary) as avg_salary
            FROM departments d 
            LEFT JOIN employees e ON d.id = e.department_id 
            GROUP BY d.id
            ORDER BY avg_salary DESC
            """,
            # Группировка и сортировка (влияние work_mem)
            """
            SELECT e.department_id, e.position, COUNT(*) as cnt, AVG(e.salary) as avg_salary
            FROM employees e
            GROUP BY e.department_id, e.position
            ORDER BY avg_salary DESC
            LIMIT 50
            """,
        ],
        'complex': [
            # Многослойная агрегация (влияние work_mem, shared_buffers)
            """
            SELECT 
                d.dept_name,
                e.position,
                COUNT(*) as emp_count,
                AVG(e.salary) as avg_salary,
                MIN(e.salary) as min_salary,
                MAX(e.salary) as max_salary,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) as median_salary
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            GROUP BY d.id, e.position
            HAVING COUNT(*) > 5
            ORDER BY avg_salary DESC
            LIMIT 50
            """,
            # Оконные функции (влияние work_mem, random_page_cost)
            """
            WITH ranked_employees AS (
                SELECT 
                    e.first_name || ' ' || e.last_name as employee_name,
                    d.dept_name,
                    e.salary,
                    ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY e.salary DESC) as rank_in_dept,
                    RANK() OVER (ORDER BY e.salary DESC) as overall_rank
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                WHERE e.is_active = true
            )
            SELECT employee_name, dept_name, salary, rank_in_dept, overall_rank
            FROM ranked_employees
            WHERE rank_in_dept <= 5
            ORDER BY overall_rank
            LIMIT 50
            """,
            # Подзапросы и корреляция
            """
            SELECT 
                d.dept_name,
                d.budget,
                (SELECT COUNT(*) FROM employees WHERE department_id = d.id) as emp_count,
                (SELECT AVG(salary) FROM employees WHERE department_id = d.id) as avg_salary,
                (SELECT MAX(salary) FROM employees WHERE department_id = d.id) as max_salary
            FROM departments d
            WHERE d.budget > 500000
            ORDER BY avg_salary DESC
            """,
        ],
        'very_complex': [
            # Анализ распределения зарплат (оконные функции + подзапросы)
            """
            WITH salary_stats AS (
                SELECT 
                    department_id,
                    salary,
                    NTILE(4) OVER (PARTITION BY department_id ORDER BY salary) as salary_quartile
                FROM employees
                WHERE is_active = true
            ),
            dept_stats AS (
                SELECT 
                    d.id,
                    d.dept_name,
                    AVG(ss.salary) as avg_salary,
                    STDDEV(ss.salary) as salary_stddev,
                    COUNT(CASE WHEN ss.salary_quartile = 4 THEN 1 END) as top_quarter_count
                FROM departments d
                JOIN salary_stats ss ON d.id = ss.department_id
                GROUP BY d.id, d.dept_name
            )
            SELECT 
                dept_name,
                avg_salary,
                salary_stddev,
                top_quarter_count,
                RANK() OVER (ORDER BY avg_salary DESC) as salary_rank
            FROM dept_stats
            ORDER BY salary_rank
            LIMIT 20
            """,
        ],
    }