#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Простая схема базы данных (2 таблицы)"""
import random
from datetime import datetime, timedelta

def create_tables(cursor):
    """Создаёт простые таблицы"""
    
    # Таблица отделов
    cursor.execute("""
        DROP TABLE IF EXISTS employees CASCADE;
        DROP TABLE IF EXISTS departments CASCADE;
    """)
    
    cursor.execute("""
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            dept_code VARCHAR(10) NOT NULL UNIQUE,
            dept_name VARCHAR(100) NOT NULL,
            location VARCHAR(100)
        )
    """)
    
    # Таблица сотрудников
    cursor.execute("""
        CREATE TABLE employees (
            id SERIAL PRIMARY KEY,
            emp_id VARCHAR(20) NOT NULL UNIQUE,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            department_id INTEGER REFERENCES departments(id),
            salary NUMERIC(10,2),
            hire_date DATE
        )
    """)
    
    cursor.execute("CREATE INDEX idx_emp_dept ON employees(department_id);")
    
    print("Простая схема создана (2 таблицы)")


def generate_data(cursor, counts: dict):
    """Генерирует тестовые данные"""
    
    # Отделы
    departments = [
        ('IT', 'Information Technology', 'Moscow'),
        ('HR', 'Human Resources', 'Moscow'),
        ('SALES', 'Sales', 'Saint Petersburg'),
        ('FIN', 'Finance', 'Moscow'),
        ('OPS', 'Operations', 'Kazan'),
    ]
    
    for dept in departments:
        cursor.execute("""
            INSERT INTO departments (dept_code, dept_name, location)
            VALUES (%s, %s, %s)
        """, dept)
    
    # Сотрудники
    first_names = ['Иван', 'Петр', 'Анна', 'Мария', 'Алексей', 'Елена', 'Дмитрий', 'Ольга']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Кузнецова', 'Смирнов', 'Волкова']
    
    for i in range(counts.get('employees', 100)):
        emp_id = f"EMP{str(i+1).zfill(5)}"
        first = first_names[i % len(first_names)]
        last = last_names[i % len(last_names)]
        dept_id = (i % 5) + 1
        salary = 30000 + (i % 70000)
        hire_date = f"2020-01-01"
        
        cursor.execute("""
            INSERT INTO employees (emp_id, first_name, last_name, department_id, salary, hire_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_id, first, last, dept_id, salary, hire_date))


def get_test_queries():
    """Возвращает запросы для тестирования этой схемы"""
    
    return {
        'simple': [
            "SELECT * FROM employees LIMIT 10",
            "SELECT COUNT(*) FROM employees",
            "SELECT * FROM departments",
            "SELECT e.first_name, e.last_name, d.dept_name FROM employees e JOIN departments d ON e.department_id = d.id LIMIT 20",
        ],
        'medium': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.dept_name",
            "SELECT d.dept_name, COUNT(*) as emp_count FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.dept_name ORDER BY emp_count DESC",
        ],
        'complex': [
            "SELECT d.dept_name, COUNT(*) as emp_count, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.dept_name HAVING COUNT(*) > 5",
        ],
    }
    
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
            "SELECT e.first_name, e.last_name, d.dept_name FROM employees e JOIN departments d ON e.department_id = d.id LIMIT 50",
            "SELECT d.dept_name, COUNT(e.id) as emp_count FROM departments d LEFT JOIN employees e ON d.id = e.department_id GROUP BY d.id",
        ],
        'complex': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.id ORDER BY avg_salary DESC",
        ],
        'very_complex': [
            "SELECT d.dept_name, AVG(e.salary) as avg_salary, COUNT(e.id) as emp_count FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.id HAVING COUNT(e.id) > 5",
        ],
    }